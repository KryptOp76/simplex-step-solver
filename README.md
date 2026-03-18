# simplex-step-solver
A step-by-step Simplex Method solver developed as a task for MAT316: Operations Research at BRAC University. This applet generates successive simplex tables until an optimal solution is reached or the problem is concluded to be unbounded, following the specific tabular notation learned in class.

## ✨ Key Features
* **Successive Tables:** Generates every iteration of the simplex table one-by-one.
* **Optimization Types:** Supports both **Maximization** and **Minimization** problems.
* **Edge Case Detection:** Identifies when a problem has no finite limit.
    * **Degeneracy & Cycling:** Detects infinite loops in highly degenerate LPPs.
    * **Infeasibility:** Validates initial basic solutions for non-negative RHS values.
