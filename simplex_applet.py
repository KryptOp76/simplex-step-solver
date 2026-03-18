import numpy as np
import streamlit as st
import pandas as pd

def get_pivot_column(tab, problem_type):
    """Finds the entering variable based on optimization type."""
    z_row = tab[-1]
    variable_cols = z_row[:-1]
    
    if problem_type == "Minimize":
        # Minimization: Choose most negative. Stop if all >= 0
        min_val = np.min(variable_cols)
        if min_val >= 0:
            return -1 
        return np.argmin(variable_cols)
    else:
        # Maximization: Choose most positive. Stop if all <= 0
        max_val = np.max(variable_cols)
        if max_val <= 0:
            return -1
        return np.argmax(variable_cols)

def get_pivot_row(tab, pivot_col):
    """Finds the leaving variable using the minimum positive ratio test."""
    rhs_col = tab[:-1, -1]
    p_col_vals = tab[:-1, pivot_col]
    ratios = []
    for i in range(len(p_col_vals)):
        # We only consider strictly positive entries in the pivot column
        if p_col_vals[i] > 1e-7: 
            ratio = rhs_col[i] / p_col_vals[i]
            ratios.append(ratio)
        else:
            ratios.append(np.inf) 
    if all(r == np.inf for r in ratios):
        return -1 
    pivot_row = np.argmin(ratios)
    return pivot_row

def perform_pivot(tab, pivot_row, pivot_col):
    next_tab = np.copy(tab)
    pivot_element = next_tab[pivot_row, pivot_col]
    next_tab[pivot_row] = next_tab[pivot_row] / pivot_element
    for r in range(len(next_tab)):
        if r != pivot_row:
            multiplier = next_tab[r, pivot_col]
            next_tab[r] = next_tab[r] - (multiplier * next_tab[pivot_row])
    return next_tab

def solve_simplex(initial_tableau, problem_type):
    tables = [np.copy(initial_tableau)]
    current_tab = np.copy(initial_tableau)
    iteration = 1
    status = "Solving..."
    
    if np.any(current_tab[:-1, -1] < -1e-7):
        return tables, "Infeasible Initial Basic Solution"
        
    max_iterations = 100 
    
    while iteration <= max_iterations:
        # Pass the problem_type to apply the correct column logic
        p_col = get_pivot_column(current_tab, problem_type)
        if p_col == -1:
            status = f"Optimal Solution Reached ({problem_type})"
            break
            
        p_row = get_pivot_row(current_tab, p_col)
        if p_row == -1:
            status = f"Problem is Unbounded ({problem_type})"
            break
            
        current_tab = perform_pivot(current_tab, p_row, p_col)
        tables.append(np.copy(current_tab))
        iteration += 1
        
    if iteration > max_iterations:
        status = "Cycling Detected (Infinite Loop)"
        
    return tables, status

def get_tableau_labels(tab):
    """Dynamically generates column and row labels for the Simplex tableau."""
    num_rows, num_cols = tab.shape
    cols = [f"x{j+1}" for j in range(num_cols - 1)] + ["RHS"]
    
    rows = []
    for i in range(num_rows - 1):
        basis_var = f"Row {i+1}"
        for j in range(num_cols - 1):
            if np.isclose(tab[i, j], 1.0) and np.isclose(np.sum(np.abs(tab[:, j])), 1.0):
                basis_var = f"x{j+1}"
                break
        rows.append(basis_var)
    rows.append("Z") 
    
    return cols, rows

# --- STREAMLIT APPLET UI ---
st.title("Simplex Method Step-by-Step Solver")
st.markdown("""
Enter your initial canonical form below (comma-separated values, one row per line).
            
💡 **Note:** The applet supports any number of variables and constraints! Just make sure every row has the same number of columns.
            
📝 **Equation Format:** Assume the objective equation is in the form: $\\sum(c_ix_i) = \\text{Constant} + Z$
""")

# --- User selects optimization type ---
problem_type = st.radio("Optimization Type:", ("Minimize", "Maximize"))

default_matrix = "1.0, 1.0, 1.0, 0.0, 4.0\n1.0, -1.0, 0.0, 1.0, 2.0\n-3.0, -2.0, 0.0, 0.0, 0.0"
user_input = st.text_area("Initial Canonical Form:", value=default_matrix, height=150)

if st.button("Solve"):
    try:
        rows = user_input.strip().split('\n')
        matrix_data = [[float(val.strip()) for val in row.split(',')] for row in rows]
        initial_tableau = np.array(matrix_data)
        
        # Pass the selected problem_type into the solver
        all_tables, final_status = solve_simplex(initial_tableau, problem_type)
        
        st.subheader(f"Status: {final_status}")
        
        for i, tab in enumerate(all_tables):
            if i == 0:
                st.write("**Initial Canonical Form**")
            else:
                st.write(f"**Canonical Form after Iteration {i}**")
            
            col_labels, row_labels = get_tableau_labels(tab)
            df = pd.DataFrame(tab, columns=col_labels, index=row_labels)
            st.dataframe(df.style.format("{:.3f}"))

        # --- Final Solution Summary ---
        if "Optimal" in final_status:
            st.success("✨ Optimal Solution Found!")
            final_tab = all_tables[-1]
            final_cols, final_rows = get_tableau_labels(final_tab)
            
            # Initialize all variables to 0.0
            solution = {col: 0.0 for col in final_cols[:-1]} 
            
            # Update values for the basic variables using the RHS column
            for idx, basis_var in enumerate(final_rows[:-1]):
                if basis_var in solution:
                    solution[basis_var] = final_tab[idx, -1]
                    
            # The optimal Z value is in the bottom right corner
            optimal_z = final_tab[-1, -1]

            # In this canonical form, the true Z is always the negative of the RHS constant
            optimal_z = optimal_z * -1
            
            # Display the summary box
            st.markdown("### Optimal Solution Summary")
            col1, col2 = st.columns(2)
            
            with col1:
                for var, val in solution.items():
                    st.write(f"**{var}** = {val:.3f}")
            with col2:
                st.write(f"**Optimal Z** = {optimal_z:.3f}")
                
        # --- Unbounded Conclusion ---
        elif "Unbounded" in final_status:
            st.error("🚨 Conclusion: The problem is Unbounded.")
            if problem_type == "Minimize":
                st.write("There is no limit of increase for the entering variable. It can be increased indefinitely and $Z$ keeps decreasing. Therefore, the LPP is unbounded ($Z \\to -\\infty$).")
            else:
                st.write("There is no limit of increase for the entering variable. It can be increased indefinitely and $Z$ keeps increasing. Therefore, the LPP is unbounded ($Z \\to \\infty$).")
                
        # --- Feasibility Conclusion ---
        elif "Infeasible" in final_status:
            st.error("🚨 Conclusion: Infeasible Initial Basic Solution.")
            st.write("The standard Simplex method requires all Right-Hand Side (RHS) values to be non-negative ($\\ge 0$) to start.")
            
        # --- Cycling Conclusion ---
        elif "Cycling" in final_status:
            st.error("🚨 Conclusion: Cycling Detected (Infinite Loop).")
            st.write("The algorithm hit the maximum iteration limit (100). It is pivoting through a sequence of basic feasible solutions without improving the objective value ($Z$), resulting in an infinite loop.")
            
    except Exception as e:
        st.error(f"Error parsing matrix. Please ensure it is formatted as comma-separated numbers.")

# --- FOOTER ---
st.markdown("---")
footer_html = """
<div style='text-align: center;'>
    <p style='color: #888888; margin-bottom: 5px;'>Developed by <b>Irfan Rahman Rasib</b></p>
    <a href="https://github.com/KryptOp76/simplex-step-solver" target="_blank">
        <img src="https://img.shields.io/badge/GitHub-View_Repository-181717?logo=github" alt="GitHub Repository">
    </a>
</div>
"""
st.markdown(footer_html, unsafe_allow_html=True)