# Generated from C:/Users/cuent/OneDrive - Estudiantes ITCR/Compiladores e Interpretes/Proyecto Compiladores/rustiq-compiler/grammar/RustiQ.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .RustiQParser import RustiQParser
else:
    from RustiQParser import RustiQParser

# This class defines a complete listener for a parse tree produced by RustiQParser.
class RustiQListener(ParseTreeListener):

    # Enter a parse tree produced by RustiQParser#program.
    def enterProgram(self, ctx:RustiQParser.ProgramContext):
        pass

    # Exit a parse tree produced by RustiQParser#program.
    def exitProgram(self, ctx:RustiQParser.ProgramContext):
        pass


    # Enter a parse tree produced by RustiQParser#item.
    def enterItem(self, ctx:RustiQParser.ItemContext):
        pass

    # Exit a parse tree produced by RustiQParser#item.
    def exitItem(self, ctx:RustiQParser.ItemContext):
        pass


    # Enter a parse tree produced by RustiQParser#functionDecl.
    def enterFunctionDecl(self, ctx:RustiQParser.FunctionDeclContext):
        pass

    # Exit a parse tree produced by RustiQParser#functionDecl.
    def exitFunctionDecl(self, ctx:RustiQParser.FunctionDeclContext):
        pass


    # Enter a parse tree produced by RustiQParser#parameterList.
    def enterParameterList(self, ctx:RustiQParser.ParameterListContext):
        pass

    # Exit a parse tree produced by RustiQParser#parameterList.
    def exitParameterList(self, ctx:RustiQParser.ParameterListContext):
        pass


    # Enter a parse tree produced by RustiQParser#parameter.
    def enterParameter(self, ctx:RustiQParser.ParameterContext):
        pass

    # Exit a parse tree produced by RustiQParser#parameter.
    def exitParameter(self, ctx:RustiQParser.ParameterContext):
        pass


    # Enter a parse tree produced by RustiQParser#constDecl.
    def enterConstDecl(self, ctx:RustiQParser.ConstDeclContext):
        pass

    # Exit a parse tree produced by RustiQParser#constDecl.
    def exitConstDecl(self, ctx:RustiQParser.ConstDeclContext):
        pass


    # Enter a parse tree produced by RustiQParser#structDecl.
    def enterStructDecl(self, ctx:RustiQParser.StructDeclContext):
        pass

    # Exit a parse tree produced by RustiQParser#structDecl.
    def exitStructDecl(self, ctx:RustiQParser.StructDeclContext):
        pass


    # Enter a parse tree produced by RustiQParser#fieldDecl.
    def enterFieldDecl(self, ctx:RustiQParser.FieldDeclContext):
        pass

    # Exit a parse tree produced by RustiQParser#fieldDecl.
    def exitFieldDecl(self, ctx:RustiQParser.FieldDeclContext):
        pass


    # Enter a parse tree produced by RustiQParser#enumDecl.
    def enterEnumDecl(self, ctx:RustiQParser.EnumDeclContext):
        pass

    # Exit a parse tree produced by RustiQParser#enumDecl.
    def exitEnumDecl(self, ctx:RustiQParser.EnumDeclContext):
        pass


    # Enter a parse tree produced by RustiQParser#variantDecl.
    def enterVariantDecl(self, ctx:RustiQParser.VariantDeclContext):
        pass

    # Exit a parse tree produced by RustiQParser#variantDecl.
    def exitVariantDecl(self, ctx:RustiQParser.VariantDeclContext):
        pass


    # Enter a parse tree produced by RustiQParser#typeList.
    def enterTypeList(self, ctx:RustiQParser.TypeListContext):
        pass

    # Exit a parse tree produced by RustiQParser#typeList.
    def exitTypeList(self, ctx:RustiQParser.TypeListContext):
        pass


    # Enter a parse tree produced by RustiQParser#PrimitiveT.
    def enterPrimitiveT(self, ctx:RustiQParser.PrimitiveTContext):
        pass

    # Exit a parse tree produced by RustiQParser#PrimitiveT.
    def exitPrimitiveT(self, ctx:RustiQParser.PrimitiveTContext):
        pass


    # Enter a parse tree produced by RustiQParser#StringT.
    def enterStringT(self, ctx:RustiQParser.StringTContext):
        pass

    # Exit a parse tree produced by RustiQParser#StringT.
    def exitStringT(self, ctx:RustiQParser.StringTContext):
        pass


    # Enter a parse tree produced by RustiQParser#ArrayT.
    def enterArrayT(self, ctx:RustiQParser.ArrayTContext):
        pass

    # Exit a parse tree produced by RustiQParser#ArrayT.
    def exitArrayT(self, ctx:RustiQParser.ArrayTContext):
        pass


    # Enter a parse tree produced by RustiQParser#TupleT.
    def enterTupleT(self, ctx:RustiQParser.TupleTContext):
        pass

    # Exit a parse tree produced by RustiQParser#TupleT.
    def exitTupleT(self, ctx:RustiQParser.TupleTContext):
        pass


    # Enter a parse tree produced by RustiQParser#RefT.
    def enterRefT(self, ctx:RustiQParser.RefTContext):
        pass

    # Exit a parse tree produced by RustiQParser#RefT.
    def exitRefT(self, ctx:RustiQParser.RefTContext):
        pass


    # Enter a parse tree produced by RustiQParser#NamedT.
    def enterNamedT(self, ctx:RustiQParser.NamedTContext):
        pass

    # Exit a parse tree produced by RustiQParser#NamedT.
    def exitNamedT(self, ctx:RustiQParser.NamedTContext):
        pass


    # Enter a parse tree produced by RustiQParser#primitiveType.
    def enterPrimitiveType(self, ctx:RustiQParser.PrimitiveTypeContext):
        pass

    # Exit a parse tree produced by RustiQParser#primitiveType.
    def exitPrimitiveType(self, ctx:RustiQParser.PrimitiveTypeContext):
        pass


    # Enter a parse tree produced by RustiQParser#block.
    def enterBlock(self, ctx:RustiQParser.BlockContext):
        pass

    # Exit a parse tree produced by RustiQParser#block.
    def exitBlock(self, ctx:RustiQParser.BlockContext):
        pass


    # Enter a parse tree produced by RustiQParser#LetStmt.
    def enterLetStmt(self, ctx:RustiQParser.LetStmtContext):
        pass

    # Exit a parse tree produced by RustiQParser#LetStmt.
    def exitLetStmt(self, ctx:RustiQParser.LetStmtContext):
        pass


    # Enter a parse tree produced by RustiQParser#ConstStmt.
    def enterConstStmt(self, ctx:RustiQParser.ConstStmtContext):
        pass

    # Exit a parse tree produced by RustiQParser#ConstStmt.
    def exitConstStmt(self, ctx:RustiQParser.ConstStmtContext):
        pass


    # Enter a parse tree produced by RustiQParser#AssignStmt.
    def enterAssignStmt(self, ctx:RustiQParser.AssignStmtContext):
        pass

    # Exit a parse tree produced by RustiQParser#AssignStmt.
    def exitAssignStmt(self, ctx:RustiQParser.AssignStmtContext):
        pass


    # Enter a parse tree produced by RustiQParser#ExprStmt.
    def enterExprStmt(self, ctx:RustiQParser.ExprStmtContext):
        pass

    # Exit a parse tree produced by RustiQParser#ExprStmt.
    def exitExprStmt(self, ctx:RustiQParser.ExprStmtContext):
        pass


    # Enter a parse tree produced by RustiQParser#ReturnS.
    def enterReturnS(self, ctx:RustiQParser.ReturnSContext):
        pass

    # Exit a parse tree produced by RustiQParser#ReturnS.
    def exitReturnS(self, ctx:RustiQParser.ReturnSContext):
        pass


    # Enter a parse tree produced by RustiQParser#BreakS.
    def enterBreakS(self, ctx:RustiQParser.BreakSContext):
        pass

    # Exit a parse tree produced by RustiQParser#BreakS.
    def exitBreakS(self, ctx:RustiQParser.BreakSContext):
        pass


    # Enter a parse tree produced by RustiQParser#ContinueS.
    def enterContinueS(self, ctx:RustiQParser.ContinueSContext):
        pass

    # Exit a parse tree produced by RustiQParser#ContinueS.
    def exitContinueS(self, ctx:RustiQParser.ContinueSContext):
        pass


    # Enter a parse tree produced by RustiQParser#WhileS.
    def enterWhileS(self, ctx:RustiQParser.WhileSContext):
        pass

    # Exit a parse tree produced by RustiQParser#WhileS.
    def exitWhileS(self, ctx:RustiQParser.WhileSContext):
        pass


    # Enter a parse tree produced by RustiQParser#LoopS.
    def enterLoopS(self, ctx:RustiQParser.LoopSContext):
        pass

    # Exit a parse tree produced by RustiQParser#LoopS.
    def exitLoopS(self, ctx:RustiQParser.LoopSContext):
        pass


    # Enter a parse tree produced by RustiQParser#IfS.
    def enterIfS(self, ctx:RustiQParser.IfSContext):
        pass

    # Exit a parse tree produced by RustiQParser#IfS.
    def exitIfS(self, ctx:RustiQParser.IfSContext):
        pass


    # Enter a parse tree produced by RustiQParser#BlockS.
    def enterBlockS(self, ctx:RustiQParser.BlockSContext):
        pass

    # Exit a parse tree produced by RustiQParser#BlockS.
    def exitBlockS(self, ctx:RustiQParser.BlockSContext):
        pass


    # Enter a parse tree produced by RustiQParser#letDecl.
    def enterLetDecl(self, ctx:RustiQParser.LetDeclContext):
        pass

    # Exit a parse tree produced by RustiQParser#letDecl.
    def exitLetDecl(self, ctx:RustiQParser.LetDeclContext):
        pass


    # Enter a parse tree produced by RustiQParser#constLocalDecl.
    def enterConstLocalDecl(self, ctx:RustiQParser.ConstLocalDeclContext):
        pass

    # Exit a parse tree produced by RustiQParser#constLocalDecl.
    def exitConstLocalDecl(self, ctx:RustiQParser.ConstLocalDeclContext):
        pass


    # Enter a parse tree produced by RustiQParser#assignment.
    def enterAssignment(self, ctx:RustiQParser.AssignmentContext):
        pass

    # Exit a parse tree produced by RustiQParser#assignment.
    def exitAssignment(self, ctx:RustiQParser.AssignmentContext):
        pass


    # Enter a parse tree produced by RustiQParser#assignOp.
    def enterAssignOp(self, ctx:RustiQParser.AssignOpContext):
        pass

    # Exit a parse tree produced by RustiQParser#assignOp.
    def exitAssignOp(self, ctx:RustiQParser.AssignOpContext):
        pass


    # Enter a parse tree produced by RustiQParser#returnStmt.
    def enterReturnStmt(self, ctx:RustiQParser.ReturnStmtContext):
        pass

    # Exit a parse tree produced by RustiQParser#returnStmt.
    def exitReturnStmt(self, ctx:RustiQParser.ReturnStmtContext):
        pass


    # Enter a parse tree produced by RustiQParser#breakStmt.
    def enterBreakStmt(self, ctx:RustiQParser.BreakStmtContext):
        pass

    # Exit a parse tree produced by RustiQParser#breakStmt.
    def exitBreakStmt(self, ctx:RustiQParser.BreakStmtContext):
        pass


    # Enter a parse tree produced by RustiQParser#continueStmt.
    def enterContinueStmt(self, ctx:RustiQParser.ContinueStmtContext):
        pass

    # Exit a parse tree produced by RustiQParser#continueStmt.
    def exitContinueStmt(self, ctx:RustiQParser.ContinueStmtContext):
        pass


    # Enter a parse tree produced by RustiQParser#whileStmt.
    def enterWhileStmt(self, ctx:RustiQParser.WhileStmtContext):
        pass

    # Exit a parse tree produced by RustiQParser#whileStmt.
    def exitWhileStmt(self, ctx:RustiQParser.WhileStmtContext):
        pass


    # Enter a parse tree produced by RustiQParser#loopStmt.
    def enterLoopStmt(self, ctx:RustiQParser.LoopStmtContext):
        pass

    # Exit a parse tree produced by RustiQParser#loopStmt.
    def exitLoopStmt(self, ctx:RustiQParser.LoopStmtContext):
        pass


    # Enter a parse tree produced by RustiQParser#ifStmt.
    def enterIfStmt(self, ctx:RustiQParser.IfStmtContext):
        pass

    # Exit a parse tree produced by RustiQParser#ifStmt.
    def exitIfStmt(self, ctx:RustiQParser.IfStmtContext):
        pass


    # Enter a parse tree produced by RustiQParser#condition.
    def enterCondition(self, ctx:RustiQParser.ConditionContext):
        pass

    # Exit a parse tree produced by RustiQParser#condition.
    def exitCondition(self, ctx:RustiQParser.ConditionContext):
        pass


    # Enter a parse tree produced by RustiQParser#expression.
    def enterExpression(self, ctx:RustiQParser.ExpressionContext):
        pass

    # Exit a parse tree produced by RustiQParser#expression.
    def exitExpression(self, ctx:RustiQParser.ExpressionContext):
        pass


    # Enter a parse tree produced by RustiQParser#logicalOr.
    def enterLogicalOr(self, ctx:RustiQParser.LogicalOrContext):
        pass

    # Exit a parse tree produced by RustiQParser#logicalOr.
    def exitLogicalOr(self, ctx:RustiQParser.LogicalOrContext):
        pass


    # Enter a parse tree produced by RustiQParser#logicalAnd.
    def enterLogicalAnd(self, ctx:RustiQParser.LogicalAndContext):
        pass

    # Exit a parse tree produced by RustiQParser#logicalAnd.
    def exitLogicalAnd(self, ctx:RustiQParser.LogicalAndContext):
        pass


    # Enter a parse tree produced by RustiQParser#comparison.
    def enterComparison(self, ctx:RustiQParser.ComparisonContext):
        pass

    # Exit a parse tree produced by RustiQParser#comparison.
    def exitComparison(self, ctx:RustiQParser.ComparisonContext):
        pass


    # Enter a parse tree produced by RustiQParser#relOp.
    def enterRelOp(self, ctx:RustiQParser.RelOpContext):
        pass

    # Exit a parse tree produced by RustiQParser#relOp.
    def exitRelOp(self, ctx:RustiQParser.RelOpContext):
        pass


    # Enter a parse tree produced by RustiQParser#additive.
    def enterAdditive(self, ctx:RustiQParser.AdditiveContext):
        pass

    # Exit a parse tree produced by RustiQParser#additive.
    def exitAdditive(self, ctx:RustiQParser.AdditiveContext):
        pass


    # Enter a parse tree produced by RustiQParser#multiplicative.
    def enterMultiplicative(self, ctx:RustiQParser.MultiplicativeContext):
        pass

    # Exit a parse tree produced by RustiQParser#multiplicative.
    def exitMultiplicative(self, ctx:RustiQParser.MultiplicativeContext):
        pass


    # Enter a parse tree produced by RustiQParser#unary.
    def enterUnary(self, ctx:RustiQParser.UnaryContext):
        pass

    # Exit a parse tree produced by RustiQParser#unary.
    def exitUnary(self, ctx:RustiQParser.UnaryContext):
        pass


    # Enter a parse tree produced by RustiQParser#postfix.
    def enterPostfix(self, ctx:RustiQParser.PostfixContext):
        pass

    # Exit a parse tree produced by RustiQParser#postfix.
    def exitPostfix(self, ctx:RustiQParser.PostfixContext):
        pass


    # Enter a parse tree produced by RustiQParser#callSuffix.
    def enterCallSuffix(self, ctx:RustiQParser.CallSuffixContext):
        pass

    # Exit a parse tree produced by RustiQParser#callSuffix.
    def exitCallSuffix(self, ctx:RustiQParser.CallSuffixContext):
        pass


    # Enter a parse tree produced by RustiQParser#argumentList.
    def enterArgumentList(self, ctx:RustiQParser.ArgumentListContext):
        pass

    # Exit a parse tree produced by RustiQParser#argumentList.
    def exitArgumentList(self, ctx:RustiQParser.ArgumentListContext):
        pass


    # Enter a parse tree produced by RustiQParser#fieldSuffix.
    def enterFieldSuffix(self, ctx:RustiQParser.FieldSuffixContext):
        pass

    # Exit a parse tree produced by RustiQParser#fieldSuffix.
    def exitFieldSuffix(self, ctx:RustiQParser.FieldSuffixContext):
        pass


    # Enter a parse tree produced by RustiQParser#indexSuffix.
    def enterIndexSuffix(self, ctx:RustiQParser.IndexSuffixContext):
        pass

    # Exit a parse tree produced by RustiQParser#indexSuffix.
    def exitIndexSuffix(self, ctx:RustiQParser.IndexSuffixContext):
        pass


    # Enter a parse tree produced by RustiQParser#LiteralP.
    def enterLiteralP(self, ctx:RustiQParser.LiteralPContext):
        pass

    # Exit a parse tree produced by RustiQParser#LiteralP.
    def exitLiteralP(self, ctx:RustiQParser.LiteralPContext):
        pass


    # Enter a parse tree produced by RustiQParser#StructP.
    def enterStructP(self, ctx:RustiQParser.StructPContext):
        pass

    # Exit a parse tree produced by RustiQParser#StructP.
    def exitStructP(self, ctx:RustiQParser.StructPContext):
        pass


    # Enter a parse tree produced by RustiQParser#EnumP.
    def enterEnumP(self, ctx:RustiQParser.EnumPContext):
        pass

    # Exit a parse tree produced by RustiQParser#EnumP.
    def exitEnumP(self, ctx:RustiQParser.EnumPContext):
        pass


    # Enter a parse tree produced by RustiQParser#IdentP.
    def enterIdentP(self, ctx:RustiQParser.IdentPContext):
        pass

    # Exit a parse tree produced by RustiQParser#IdentP.
    def exitIdentP(self, ctx:RustiQParser.IdentPContext):
        pass


    # Enter a parse tree produced by RustiQParser#TupleP.
    def enterTupleP(self, ctx:RustiQParser.TuplePContext):
        pass

    # Exit a parse tree produced by RustiQParser#TupleP.
    def exitTupleP(self, ctx:RustiQParser.TuplePContext):
        pass


    # Enter a parse tree produced by RustiQParser#ArrayP.
    def enterArrayP(self, ctx:RustiQParser.ArrayPContext):
        pass

    # Exit a parse tree produced by RustiQParser#ArrayP.
    def exitArrayP(self, ctx:RustiQParser.ArrayPContext):
        pass


    # Enter a parse tree produced by RustiQParser#MatchP.
    def enterMatchP(self, ctx:RustiQParser.MatchPContext):
        pass

    # Exit a parse tree produced by RustiQParser#MatchP.
    def exitMatchP(self, ctx:RustiQParser.MatchPContext):
        pass


    # Enter a parse tree produced by RustiQParser#ParenP.
    def enterParenP(self, ctx:RustiQParser.ParenPContext):
        pass

    # Exit a parse tree produced by RustiQParser#ParenP.
    def exitParenP(self, ctx:RustiQParser.ParenPContext):
        pass


    # Enter a parse tree produced by RustiQParser#BlockP.
    def enterBlockP(self, ctx:RustiQParser.BlockPContext):
        pass

    # Exit a parse tree produced by RustiQParser#BlockP.
    def exitBlockP(self, ctx:RustiQParser.BlockPContext):
        pass


    # Enter a parse tree produced by RustiQParser#tupleLiteral.
    def enterTupleLiteral(self, ctx:RustiQParser.TupleLiteralContext):
        pass

    # Exit a parse tree produced by RustiQParser#tupleLiteral.
    def exitTupleLiteral(self, ctx:RustiQParser.TupleLiteralContext):
        pass


    # Enter a parse tree produced by RustiQParser#arrayLiteral.
    def enterArrayLiteral(self, ctx:RustiQParser.ArrayLiteralContext):
        pass

    # Exit a parse tree produced by RustiQParser#arrayLiteral.
    def exitArrayLiteral(self, ctx:RustiQParser.ArrayLiteralContext):
        pass


    # Enter a parse tree produced by RustiQParser#structLiteral.
    def enterStructLiteral(self, ctx:RustiQParser.StructLiteralContext):
        pass

    # Exit a parse tree produced by RustiQParser#structLiteral.
    def exitStructLiteral(self, ctx:RustiQParser.StructLiteralContext):
        pass


    # Enter a parse tree produced by RustiQParser#fieldInit.
    def enterFieldInit(self, ctx:RustiQParser.FieldInitContext):
        pass

    # Exit a parse tree produced by RustiQParser#fieldInit.
    def exitFieldInit(self, ctx:RustiQParser.FieldInitContext):
        pass


    # Enter a parse tree produced by RustiQParser#enumValue.
    def enterEnumValue(self, ctx:RustiQParser.EnumValueContext):
        pass

    # Exit a parse tree produced by RustiQParser#enumValue.
    def exitEnumValue(self, ctx:RustiQParser.EnumValueContext):
        pass


    # Enter a parse tree produced by RustiQParser#matchExpr.
    def enterMatchExpr(self, ctx:RustiQParser.MatchExprContext):
        pass

    # Exit a parse tree produced by RustiQParser#matchExpr.
    def exitMatchExpr(self, ctx:RustiQParser.MatchExprContext):
        pass


    # Enter a parse tree produced by RustiQParser#matchArm.
    def enterMatchArm(self, ctx:RustiQParser.MatchArmContext):
        pass

    # Exit a parse tree produced by RustiQParser#matchArm.
    def exitMatchArm(self, ctx:RustiQParser.MatchArmContext):
        pass


    # Enter a parse tree produced by RustiQParser#WildcardPat.
    def enterWildcardPat(self, ctx:RustiQParser.WildcardPatContext):
        pass

    # Exit a parse tree produced by RustiQParser#WildcardPat.
    def exitWildcardPat(self, ctx:RustiQParser.WildcardPatContext):
        pass


    # Enter a parse tree produced by RustiQParser#LiteralPat.
    def enterLiteralPat(self, ctx:RustiQParser.LiteralPatContext):
        pass

    # Exit a parse tree produced by RustiQParser#LiteralPat.
    def exitLiteralPat(self, ctx:RustiQParser.LiteralPatContext):
        pass


    # Enter a parse tree produced by RustiQParser#EnumPat.
    def enterEnumPat(self, ctx:RustiQParser.EnumPatContext):
        pass

    # Exit a parse tree produced by RustiQParser#EnumPat.
    def exitEnumPat(self, ctx:RustiQParser.EnumPatContext):
        pass


    # Enter a parse tree produced by RustiQParser#BindingPat.
    def enterBindingPat(self, ctx:RustiQParser.BindingPatContext):
        pass

    # Exit a parse tree produced by RustiQParser#BindingPat.
    def exitBindingPat(self, ctx:RustiQParser.BindingPatContext):
        pass


    # Enter a parse tree produced by RustiQParser#TuplePat.
    def enterTuplePat(self, ctx:RustiQParser.TuplePatContext):
        pass

    # Exit a parse tree produced by RustiQParser#TuplePat.
    def exitTuplePat(self, ctx:RustiQParser.TuplePatContext):
        pass


    # Enter a parse tree produced by RustiQParser#patternList.
    def enterPatternList(self, ctx:RustiQParser.PatternListContext):
        pass

    # Exit a parse tree produced by RustiQParser#patternList.
    def exitPatternList(self, ctx:RustiQParser.PatternListContext):
        pass


    # Enter a parse tree produced by RustiQParser#place.
    def enterPlace(self, ctx:RustiQParser.PlaceContext):
        pass

    # Exit a parse tree produced by RustiQParser#place.
    def exitPlace(self, ctx:RustiQParser.PlaceContext):
        pass


    # Enter a parse tree produced by RustiQParser#literal.
    def enterLiteral(self, ctx:RustiQParser.LiteralContext):
        pass

    # Exit a parse tree produced by RustiQParser#literal.
    def exitLiteral(self, ctx:RustiQParser.LiteralContext):
        pass



del RustiQParser