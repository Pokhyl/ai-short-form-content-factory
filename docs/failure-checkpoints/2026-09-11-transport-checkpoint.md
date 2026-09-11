# Transport checkpoint

The first materialization attempt stopped before product changes because its expected parent file hash was incorrect. Runtime was unchanged. This is an operator transport failure, not a product failure. The corrective strategy is to use direct Git data objects from the exact current target parent and tree, then deploy stage WF02 and run a new immutable E2E.
