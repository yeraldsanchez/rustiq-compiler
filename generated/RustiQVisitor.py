# Generated from grammar/RustiQ.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .RustiQParser import RustiQParser
else:
    from RustiQParser import RustiQParser

# This class defines a complete generic visitor for a parse tree produced by RustiQParser.

class RustiQVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by RustiQParser#program.
    def visitProgram(self, ctx:RustiQParser.ProgramContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#item.
    def visitItem(self, ctx:RustiQParser.ItemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#functionDecl.
    def visitFunctionDecl(self, ctx:RustiQParser.FunctionDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#parameterList.
    def visitParameterList(self, ctx:RustiQParser.ParameterListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#parameter.
    def visitParameter(self, ctx:RustiQParser.ParameterContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#constDecl.
    def visitConstDecl(self, ctx:RustiQParser.ConstDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#structDecl.
    def visitStructDecl(self, ctx:RustiQParser.StructDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#fieldDecl.
    def visitFieldDecl(self, ctx:RustiQParser.FieldDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#enumDecl.
    def visitEnumDecl(self, ctx:RustiQParser.EnumDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#variantDecl.
    def visitVariantDecl(self, ctx:RustiQParser.VariantDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#typeList.
    def visitTypeList(self, ctx:RustiQParser.TypeListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#PrimitiveT.
    def visitPrimitiveT(self, ctx:RustiQParser.PrimitiveTContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#StringT.
    def visitStringT(self, ctx:RustiQParser.StringTContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#ArrayT.
    def visitArrayT(self, ctx:RustiQParser.ArrayTContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#TupleT.
    def visitTupleT(self, ctx:RustiQParser.TupleTContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#RefT.
    def visitRefT(self, ctx:RustiQParser.RefTContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#NamedT.
    def visitNamedT(self, ctx:RustiQParser.NamedTContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#primitiveType.
    def visitPrimitiveType(self, ctx:RustiQParser.PrimitiveTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#block.
    def visitBlock(self, ctx:RustiQParser.BlockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#LetStmt.
    def visitLetStmt(self, ctx:RustiQParser.LetStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#ConstStmt.
    def visitConstStmt(self, ctx:RustiQParser.ConstStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#AssignStmt.
    def visitAssignStmt(self, ctx:RustiQParser.AssignStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#ExprStmt.
    def visitExprStmt(self, ctx:RustiQParser.ExprStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#ReturnS.
    def visitReturnS(self, ctx:RustiQParser.ReturnSContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#BreakS.
    def visitBreakS(self, ctx:RustiQParser.BreakSContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#ContinueS.
    def visitContinueS(self, ctx:RustiQParser.ContinueSContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#WhileS.
    def visitWhileS(self, ctx:RustiQParser.WhileSContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#LoopS.
    def visitLoopS(self, ctx:RustiQParser.LoopSContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#IfS.
    def visitIfS(self, ctx:RustiQParser.IfSContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#BlockS.
    def visitBlockS(self, ctx:RustiQParser.BlockSContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#letDecl.
    def visitLetDecl(self, ctx:RustiQParser.LetDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#constLocalDecl.
    def visitConstLocalDecl(self, ctx:RustiQParser.ConstLocalDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#assignment.
    def visitAssignment(self, ctx:RustiQParser.AssignmentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#assignOp.
    def visitAssignOp(self, ctx:RustiQParser.AssignOpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#returnStmt.
    def visitReturnStmt(self, ctx:RustiQParser.ReturnStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#breakStmt.
    def visitBreakStmt(self, ctx:RustiQParser.BreakStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#continueStmt.
    def visitContinueStmt(self, ctx:RustiQParser.ContinueStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#whileStmt.
    def visitWhileStmt(self, ctx:RustiQParser.WhileStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#loopStmt.
    def visitLoopStmt(self, ctx:RustiQParser.LoopStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#ifStmt.
    def visitIfStmt(self, ctx:RustiQParser.IfStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#condition.
    def visitCondition(self, ctx:RustiQParser.ConditionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#expression.
    def visitExpression(self, ctx:RustiQParser.ExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#logicalOr.
    def visitLogicalOr(self, ctx:RustiQParser.LogicalOrContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#logicalAnd.
    def visitLogicalAnd(self, ctx:RustiQParser.LogicalAndContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#comparison.
    def visitComparison(self, ctx:RustiQParser.ComparisonContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#relOp.
    def visitRelOp(self, ctx:RustiQParser.RelOpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#additive.
    def visitAdditive(self, ctx:RustiQParser.AdditiveContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#multiplicative.
    def visitMultiplicative(self, ctx:RustiQParser.MultiplicativeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#unary.
    def visitUnary(self, ctx:RustiQParser.UnaryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#postfix.
    def visitPostfix(self, ctx:RustiQParser.PostfixContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#callSuffix.
    def visitCallSuffix(self, ctx:RustiQParser.CallSuffixContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#argumentList.
    def visitArgumentList(self, ctx:RustiQParser.ArgumentListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#fieldSuffix.
    def visitFieldSuffix(self, ctx:RustiQParser.FieldSuffixContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#indexSuffix.
    def visitIndexSuffix(self, ctx:RustiQParser.IndexSuffixContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#LiteralP.
    def visitLiteralP(self, ctx:RustiQParser.LiteralPContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#StructP.
    def visitStructP(self, ctx:RustiQParser.StructPContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#EnumP.
    def visitEnumP(self, ctx:RustiQParser.EnumPContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#IdentP.
    def visitIdentP(self, ctx:RustiQParser.IdentPContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#TupleP.
    def visitTupleP(self, ctx:RustiQParser.TuplePContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#ArrayP.
    def visitArrayP(self, ctx:RustiQParser.ArrayPContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#MatchP.
    def visitMatchP(self, ctx:RustiQParser.MatchPContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#ParenP.
    def visitParenP(self, ctx:RustiQParser.ParenPContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#BlockP.
    def visitBlockP(self, ctx:RustiQParser.BlockPContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#tupleLiteral.
    def visitTupleLiteral(self, ctx:RustiQParser.TupleLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#arrayLiteral.
    def visitArrayLiteral(self, ctx:RustiQParser.ArrayLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#structLiteral.
    def visitStructLiteral(self, ctx:RustiQParser.StructLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#fieldInit.
    def visitFieldInit(self, ctx:RustiQParser.FieldInitContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#enumValue.
    def visitEnumValue(self, ctx:RustiQParser.EnumValueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#matchExpr.
    def visitMatchExpr(self, ctx:RustiQParser.MatchExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#matchArm.
    def visitMatchArm(self, ctx:RustiQParser.MatchArmContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#WildcardPat.
    def visitWildcardPat(self, ctx:RustiQParser.WildcardPatContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#LiteralPat.
    def visitLiteralPat(self, ctx:RustiQParser.LiteralPatContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#EnumPat.
    def visitEnumPat(self, ctx:RustiQParser.EnumPatContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#BindingPat.
    def visitBindingPat(self, ctx:RustiQParser.BindingPatContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#TuplePat.
    def visitTuplePat(self, ctx:RustiQParser.TuplePatContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#patternList.
    def visitPatternList(self, ctx:RustiQParser.PatternListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#place.
    def visitPlace(self, ctx:RustiQParser.PlaceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RustiQParser#literal.
    def visitLiteral(self, ctx:RustiQParser.LiteralContext):
        return self.visitChildren(ctx)



del RustiQParser