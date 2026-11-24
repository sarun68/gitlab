# SDD ledger — plan: docs/superpowers/plans/2026-11-24-ngspice-starter.md

- Baseline: Python 3.12.7, ngspice 47, original unittest suite 4/4 passed.
- Pre-flight: Task 2 consumes Task 1's parameter object and simulation result;
  no interface conflict. CLI writes returned netlist/raw/log alongside JSON.
- Ruling: Work on a new branch in the current directory rather than create an
  unrequested worktree; only new files are added. Cost: workspace is shared,
  mitigated by preserving all existing/untracked files.
- Ruling: User's explicit "create it yourself now" is treated as authorization
  for native execution of the standalone kit, not a new round of approvals.
  Scope is the starter, not Flask integration; risk: full Lab 04 remains pending.
- Task 1: complete. Missing-module RED observed, then real ngspice exposed
  optional `grid=3` raw metadata and `i(@q1[ic])` vector naming. Added failing
  regression for metadata and restricted collector-current save to DC because
  ngspice emits scalar device parameters in complex plots. Suite 16/16 GREEN.
- Task 2: complete. Integration missing-module RED observed. Real-engine suite
  validates DC/RE, AC/transient consistency, source changes and artifacts.
  CLI produced DC + 281 AC points + 2008 transient points outside Git.
- Final review: independent general reviewer identified two important issues:
  self-consistent but shortened AC/transient output could succeed; derived DC
  VCE overflow could succeed. Both reproduced with three failing tests, then
  fixed by coverage/scale checks and derived DC finiteness checks. Suite 19/19
  GREEN including actual ngspice. No reviewer minors or declined findings.
- Final: fixed incomplete output — AC/transient regressions RED→GREEN.
- Final: fixed derived DC overflow — overflow regression RED→GREEN.
- Work retained uncommitted on lab04-spice-starter; no original files modified,
  no commits/pushes, no Flask/UI changes. All evidence paths in docs/starter-kit.md.
