import numpy as np
import streamlit as st
import pandas as pd

def format_number(val):
    """Formats numbers: integers without decimals, floats to 1 decimal place."""
    if np.isclose(val, np.round(val), atol=1e-7):
        int_val = int(np.round(val))
        # Return 0 instead of -0 for clean formatting
        return f"{0 if int_val == 0 else int_val}"
    else:
        return f"{val:.1f}"

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
    
    # --- Map normal digits to Unicode subscripts ---
    sub = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
    
    cols = [f"x{str(j+1).translate(sub)}" for j in range(num_cols - 1)] + ["RHS"]
    
    rows = []
    for i in range(num_rows - 1):
        basis_var = f"Row {i+1}"
        for j in range(num_cols - 1):
            if np.isclose(tab[i, j], 1.0) and np.isclose(np.sum(np.abs(tab[:, j])), 1.0):
                basis_var = f"x{str(j+1).translate(sub)}"
                break
        rows.append(basis_var)
    rows.append("Z") 
    
    return cols, rows

# --- STREAMLIT APPLET UI ---
st.set_page_config(page_title="Simplex Solver", layout="centered")

st.markdown("""
<style>
[data-testid="stDataFrame"] {
    border: 2px solid #164E8D;
    border-radius: 12px;
    padding: 2px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

st.title("Simplex Method Step-by-Step Solver")
st.markdown("""
Enter your initial canonical form below (comma-separated values, one row per line).
            
💡 **Note:** The applet supports any number of variables and constraints! Just make sure every row has the same number of columns. Also, you can input both integers (e.g., 3) and decimals (e.g., 2.5). The applet handles both automatically for clean tables!
            
📝 **Equation Format:** Assume the objective equation is in the form: $\\sum(c_ix_i) = \\text{Constant} + Z$
""")

# --- User selects optimization type ---
problem_type = st.radio("Optimization Type:", ("Minimize", "Maximize"))

default_matrix = "1, 1, 1, 0, 4.5\n1, -1, 0.5, 1, 2\n-3, -2, 0, 0, 0"
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
            st.write(f"**Iteration {i}**")
            
            col_labels, row_labels = get_tableau_labels(tab)
            df = pd.DataFrame(tab, columns=col_labels, index=row_labels)
            
            st.dataframe(df.style.format(format_number))

        # --- Final Solution Summary ---
        if "Optimal" in final_status:
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
            
            basic_vars = []
            non_basic_vars = []
            
            # Grab the current basis from the final row labels (excluding 'Z')
            current_basis = final_rows[:-1] 
            
            for var, val in solution.items():
                formatted_val = format_number(val)
                if var in current_basis: 
                    basic_vars.append(f"{var} = {formatted_val}")
                else:
                    non_basic_vars.append(f"{var} = {formatted_val}")
                    
            basic_vars_str = ",  ".join(basic_vars) if basic_vars else "None"
            non_basic_vars_str = ", ".join(non_basic_vars) if non_basic_vars else "None"
            
            # Determine the correct word for the Z value
            val_type = "Minimum" if problem_type == "Minimize" else "Maximum"
            
            box_html = f"""
            <style>
            .summary-container {{
                text-align: center;
                margin-top: 25px;
                margin-bottom: 20px;
            }}
            .summary-heading {{
                color: #6bbd6e;
                margin-bottom: 24px;
                font-weight: bold;
                font-size: 26px; 
                text-align: center;
            }}
            .z-badge {{
                display: inline-block;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                padding: 12px 30px;
                font-size: 22px;
                font-weight: 600;
                background-color: rgba(76, 175, 80, 0.15);
                margin-bottom: 25px;
                color: var(--text-color) !important;
            }}
            .var-info, .var-info b, .var-info i {{
                font-size: 18px; 
                line-height: 1.8;
                color: var(--text-color) !important;
            }}
            </style>
            
            <div class="summary-container">
                <div class="summary-heading">Optimal Solution Summary</div>
                <div class="z-badge">
                    {val_type} value of Z = {format_number(optimal_z)}
                </div>
                <div class="var-info">
                    <b>Basic Variables:</b> {basic_vars_str}
                </div>
                <div class="var-info">
                    <b>Non-Basic Variables:</b> {non_basic_vars_str}
                </div>
            </div>
            """
            st.markdown(box_html, unsafe_allow_html=True)
                
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