# Simplex Method Step-by-Step Solver [![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://simplex-step-solver.streamlit.app/)

A step-by-step Simplex Method solver developed as a task for MAT316: Operations Research at BRAC University. This applet generates successive simplex tables until an optimal solution is reached or the problem is concluded to be unbounded, following the specific tabular notation learned in class.

## Key Features

- **Successive Tables:** Generates every iteration of the simplex table one-by-one.
- **Optimization Types:** Supports both **Maximization** and **Minimization** problems.
- **Edge Case Detection:** Identifies when a problem has no finite limit.
  - **Degeneracy & Cycling:** Detects infinite loops in highly degenerate LPPs.
  - **Infeasibility:** Validates initial basic solutions for non-negative RHS values.

## Technical Stack

- **Language:** Python 3
- **Framework:** [Streamlit](https://streamlit.io/) (Web Interface)
- **Libraries:** NumPy & Pandas (Matrix operations and data rendering)

## Installation & Local Run

To run this applet locally, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/KryptOp76/simplex-step-solver.git](https://github.com/KryptOp76/simplex-step-solver.git)
   cd simplex-step-solver
   ```
2. **Install dependencies:**
   ```bash
   pip install streamlit pandas numpy
   ```
3. **Run the app:**
   ```bash
   streamlit run app.py
   ```
