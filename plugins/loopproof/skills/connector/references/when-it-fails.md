# When it fails

The connector module checks what it reads before it uses it, and its messages say what to do. Read the message in
the plan's or the apply's output, and follow it. The module never prints either value: a message names the parameter
or shows LoopProof's answer, never what the parameter holds. If anything in the output looks like a value, follow
rule 3 of the [rules](../SKILL.md#the-rules).

Whatever the cause, never work around a check: no `-target`, no change to the module or its arguments, no read of a
parameter. Each fix below is the person's, or the repository's.

## Contents

- [A parameter still holds the placeholder](#a-parameter-still-holds-the-placeholder)
- [A parameter holds something else than the module takes](#a-parameter-holds-something-else-than-the-module-takes)
- [LoopProof refused the registration token](#loopproof-refused-the-registration-token)
- [The machine can't reach LoopProof](#the-machine-cant-reach-loopproof)
- [A permission is missing](#a-permission-is-missing)

## A parameter still holds the placeholder

Part 2's plan or apply stops at the module's check, which names the parameter still holding `unset`.

- **Cause:** step 3 or 4 wasn't run, or was run in another account or Region than the root's provider.
- **Check:** the parameters' versions, as step 5 of the install reads them, with the root's account and Region. A
  parameter at the version Part 1 left it at was never filled there.
- **Fix:** the person runs that step again from the onboarding page, in the right account and Region. Then plan
  again.

## A parameter holds something else than the module takes

The module takes the ExternalIds as a list of one value, or two during a rotation, in the shape LoopProof issues them,
and a registration token in LoopProof's shape. Its message names the parameter, and says what it takes.

- **Cause:** a value pasted at the wrong step's prompt, or cut short.
- **Fix:** the person runs that parameter's step again from the onboarding page, which stores the value in the shape
  the module takes. Don't fix the value yourself.

## LoopProof refused the registration token

The apply creates everything else, then fails at the registration, with LoopProof's answer. The registration is left
tainted, so the next apply tries again by itself.

- **Expired:** a token is valid for 24 hours until it registers. Too long passed between sign-up and step 6, as when
  a pull request waited.
- **Replaced:** a newer token was made since this one was stored, which stopped it at once.
- **For another role:** the tenant already has another connector role, and a token registers only that one. The
  connector may have been applied before, in another account or root, or a role pasted on the onboarding page. Ask
  the person; don't install a second one.

The fix for an expired or replaced token:

1. The person gets a new registration token: from the onboarding page before LoopProof has proven the account, or from
   Settings once it has. A new token stops the one before it at once.
2. The person stores it with the page's step 4.
3. Apply again, the repository's way: the registration is tainted, so a plain apply calls again.

## The machine can't reach LoopProof

The registration is one HTTPS call, made with curl from the machine that applies. Without curl 7.76 or later, or
without HTTPS to the `registration_url` in Part 2, the apply creates everything else and fails at the registration,
naming the role's ARN and the Region.

- **Better:** apply from a machine that reaches LoopProof. Where CI applies, that is CI's runner: its image needs curl,
  and its network an HTTPS route to LoopProof's API. Propose the change if the repository holds it.
- **The paste, before LoopProof has proven the account:** the person pastes the role's ARN and the Region on the
  onboarding page, which registers the role without the call. It is theirs to do, in their browser. The root's outputs
  give both, one at a time:

  ```bash
  terraform output loopproof_connector_role_arn
  terraform output loopproof_connector_region
  ```

  After a paste, the registration stays tainted, and each later apply from that machine fails at it again, until one
  runs from a machine that can reach LoopProof.
- **After LoopProof has proven the account,** it takes no paste: registering needs a token and a machine that reaches
  LoopProof.

## A permission is missing

- **`ssm:GetParameter`** on `/loopproof/<environment>/*`: the module reads both parameters on every plan and apply.
- **`kms:Decrypt`** on the key, if the parameters use a customer-managed KMS key. The page's commands then need the
  key too: the person adds it when storing the values.
- **IAM, EventBridge or SSM** permissions to create the connector's resources.

Propose the change to the applier's role where the repository manages it, and say which permission and why. The person
decides.
