"""Enums y match: patrones, tipos de los brazos y exhaustividad.

Dueño: A (Yerald). Implementa solo los `visitX` de sus reglas; si necesita algo de
otro mixin, llama su método público y nunca copia la lógica.
"""

from rustiq.errors import E_TYPE_MISMATCH, E_UNKNOWN_TYPE
from rustiq.generated.RustiQParser import RustiQParser
from rustiq.types import TupleT, EnumT


class MatchMixin:
    def visitMatchExpr(self, ctx: RustiQParser.MatchExprContext):
        cond_type = self.visit(ctx.condition())
        
        arm_types = []
        for arm in ctx.matchArm():
            self.push_scope()
            # Evaluar el patrón para declarar variables (ej. 'a', 'l')
            self._check_pattern(arm.pattern(), cond_type)
            # Evaluar el cuerpo del brazo
            arm_type = self.visit(arm.expression())
            arm_types.append((arm_type, arm.expression()))
            self.pop_scope()

        if cond_type is None:
            return None

        # Verificar que todos los brazos devuelvan el mismo tipo
        valid_types = [t for t, _ in arm_types if t is not None]
        if not valid_types:
            return None

        first_type = valid_types[0]
        for t, expr in arm_types:
            if t is not None and t != first_type:
                self.mismatch(expr, E_TYPE_MISMATCH, first_type, t, "Brazo de match")

        self.info.expr_type.put(ctx, first_type)
        return first_type

    def _check_pattern(self, pat, target_type):
        if pat is None or target_type is None:
            return

        # Guardar el tipo del patrón para el generador de código
        self.info.expr_type.put(pat, target_type)

        # Patrón comodín: _
        if isinstance(pat, RustiQParser.WildcardPatContext):
            return

        # Patrón de variable (Binding): let x => ...
        if isinstance(pat, RustiQParser.BindingPatContext):
            sym = self.declare(pat.IDENT().getText(), target_type, False, "local", pat.IDENT())
            if sym is not None:
                self.info.symbol.put(pat, sym)
            return

        # Patrón literal: 1, "hola", true...
        if isinstance(pat, RustiQParser.LiteralPatContext):
            lit_type = self.visit(pat.literal())
            if lit_type and target_type and lit_type != target_type:
                self.mismatch(pat, E_TYPE_MISMATCH, target_type, lit_type, "Patrón literal")
            return

        # Patrón de tupla: (a, b)
        if isinstance(pat, RustiQParser.TuplePatContext):
            if not isinstance(target_type, TupleT) or len(target_type.elems) != len(pat.pattern()):
                self.error(pat, E_TYPE_MISMATCH, f"El patrón de tupla no coincide con el tipo '{target_type}'")
                return
            for sub_pat, sub_type in zip(pat.pattern(), target_type.elems):
                self._check_pattern(sub_pat, sub_type)
            return

        # Patrón de enum: Forma::Cuadrado(l)
        if isinstance(pat, RustiQParser.EnumPatContext):
            enum_name = pat.IDENT(0).getText()
            variant_name = pat.IDENT(1).getText()
            
            if not isinstance(target_type, EnumT) or target_type.name != enum_name:
                self.error(pat, E_TYPE_MISMATCH, f"Se esperaba un patrón de '{target_type}', se encontró '{enum_name}'")
                return

            enum_def = self.info.enums.get(enum_name)
            if not enum_def or variant_name not in enum_def.variants:
                self.error(pat, E_UNKNOWN_TYPE, f"Variante '{variant_name}' no existe en '{enum_name}'")
                return

            payload = enum_def.variants[variant_name]
            sub_pats = pat.patternList().pattern() if pat.patternList() else []
            
            if len(payload) != len(sub_pats):
                self.error(pat, E_TYPE_MISMATCH, f"La variante '{variant_name}' espera {len(payload)} argumentos")
                return

            for sub_pat, sub_type in zip(sub_pats, payload):
                self._check_pattern(sub_pat, sub_type)
            return