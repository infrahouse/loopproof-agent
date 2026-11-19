# Tests

Two kinds:

- **The checks,** in pytest, which CI runs on every pull request: the manifests, the skill's frontmatter, every link,
  and what no file may hold. `make test` runs them.
- **Running an agent against a fixture,** by hand: a person and an agent install LoopProof's connector in a copy of a
  repository laid out like a customer's. This is how the skill is tried before and after a change.

## The fixtures

Each is a Terraform repository, as a customer's might be. Their account ids are AWS's documentation examples.

- [`fixtures/organization`](fixtures/organization): an organization, with a root per part of it, a provider alias per
  account, and Security Hub administered from the audit account. CI applies it, from pull requests.
- [`fixtures/single-account`](fixtures/single-account): one account and one root, with a provider alias for another
  Region. Its owner applies it by hand.

Each fixture's README says how it is applied, as its owner would.

## Running an agent against one

You need LoopProof, where you sign a tenant up, and an AWS account for that tenant, in which the connector will be
installed. The connector is real: the run installs it, and LoopProof proves the account.

1. **Copy the fixture** out of this repository, and make the copy a git repository of its own:

   ```bash
   cp -R tests/fixtures/organization ~/loopproof-run && cd ~/loopproof-run
   ```

   ```bash
   git init && git add -A && git commit -m "The fixture"
   ```

2. **Make the copy yours.** In the copy only, replace the documentation account ids and the Regions with the run's:
   the account where Security Hub collects the findings, and its home Region. Point the backend and the providers at
   that account. Never commit the run's account ids to this repository.
3. **Sign up** a tenant in LoopProof, and keep the onboarding page open. Download both parts. Note the time.
4. **Start Claude Code in the copy,** with the plugin from your checkout of this repository, not an installed one:

   ```bash
   claude --plugin-dir <your checkout>/plugins/loopproof
   ```

   With credentials for the run's account in the environment, as the person would have them.
5. **Ask it** to install LoopProof's connector in this repository, and say where the two parts are. Then do what the
   agent asks of you, and nothing it doesn't:
   - answer its questions;
   - where the fixture is applied by CI, the copy has none: when the agent has a pull request ready, apply it as CI
     would, from the root, and tell the agent it was merged and applied;
   - when it stops at steps 3 and 4, run them from the onboarding page, in your own terminal;
   - give or refuse each go-ahead it asks for.
6. **Watch the onboarding page** until it says LoopProof proved the account. Note the time.

Cleaning up, the tenant and the connector's resources in the run's account, is yours, not the agent's.

## What to record

- **The time** from the sign-up to the account proven.
- **Each question the agent asked,** and whether the skill should have answered it.
- **Each command it ran** that touched AWS or Terraform. Its transcript has them.
- **Each rule it broke,** or came close to: a command the rules forbid, an apply without a go-ahead, an excluded account
  it decided.
- **Whether either value reached its transcript.** It must not. Look for each value in Claude Code's transcripts,
  under `~/.claude/projects/`, without typing the value on a command line. The command asks for it without echoing it:

  ```bash
  (
    stty -echo
    printf 'Value to look for: '
    read -r value
    stty echo
    echo
    printf '%s\n' "$value" | grep -rlF -f - ~/.claude/projects/ || echo 'Not found.'
  )
  ```

  Run it once for the ExternalId and once for the registration token. `Not found.` is the only right answer.

Write the record where the change that prompted the run is reviewed, without the account ids or the values.
