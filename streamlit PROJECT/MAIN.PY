import base64
import os
import plotly.express as px
import pandas as pd
import seaborn as sns
import streamlit as st

# --- Page Config (MUST be the first Streamlit command) ---
st.set_page_config(
    page_title="Automated Data Analyzer", page_icon="📊", layout="wide"
)

# --- Custom Background (Image + Overlay) ---
background_image = "Dark.png"  # <-- change to your image path
if os.path.exists(background_image):
  with open(background_image, "rb") as img_file:
    img_bytes = img_file.read()
  img_base64 = base64.b64encode(img_bytes).decode()
  page_bg = f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background: 
            linear-gradient(rgba(0,0,0,0.55), rgba(0,0,0,0.55)),  /* Dark overlay */
            url("data:image/png;base64,{img_base64}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        color: #f5f5f5;  /* Global light text */
    }}
    
    /* Header */
    [data-testid="stHeader"] {{
        background: rgba(32, 201, 151, 0.8);  /* Teal translucent */
        color: white;
    }}
    
    /* Sidebar */
    [data-testid="stSidebar"] {{
        background: rgba(20, 20, 35, 0.9);
        color: #f5f5f5;
    }}
    [data-testid="stSidebar"] * {{
        color: #f5f5f5 !important;
    }}
    /* Titles & text */
    h1, h2, h3, h4, h5, h6 {{
        color: #20c997;  /* Bright teal */
        text-shadow: 1px 1px 4px rgba(0,0,0,0.7);
    }}
    p, label, span {{
        color: #ffffff !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.6);
    }}
    /* Buttons */
    .stButton > button {{
        background-color: #20c997;
        color: white;
        border-radius: 8px;
        font-weight: 600;
        padding: 8px 20px;
        border: none;
        transition: 0.3s;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.5);
    }}
    .stButton > button:hover {{
        background-color: #ff6f61;
        transform: scale(1.05);
    }}
    /* DataFrame Styling */
    .stDataFrame {{
        background: rgba(20,20,40,0.85);
        border-radius: 8px;
        padding: 10px;
    }}
    </style>
    """
  st.markdown(page_bg, unsafe_allow_html=True)
else:
  st.error("Background image not found. Please check the path.")

# --- Initialize Session State ---
if "df" not in st.session_state:
  st.session_state["df"] = None


# --- Data Loader Function ---
def load_data(uploaded_file):
  """Loads data from CSV or Excel file."""
  if uploaded_file.name.endswith(".csv"):
    return pd.read_csv(uploaded_file)
  else:
    return pd.read_excel(uploaded_file)


# --- Title & Description ---
st.markdown(
    """
    <div style="text-align: center;">
        <h1>✨ Automated Data Analyzer & Visualization System ✨</h1>
        <p style='font-size:18px; color:#f0f0f0;'>
            Upload your dataset, explore insights, and generate beautiful graphs effortlessly 🚀
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.info("📌 Use the sidebar to navigate between pages.")

# --- Upload Section ---
st.title("📊 Data Upload & Overview")
uploaded_file = st.file_uploader(
    "📂 Upload your CSV or Excel file", type=["csv", "xlsx"]
)
st.markdown("---")
st.subheader("Or load an example dataset:")
example_dataset = st.selectbox(
    "Choose an example dataset:",
    ["None", "Iris", "Tips", "Titanic"],
    key="example_data_selector",
)

# --- Handle Data Loading ---
df_loaded = None
if uploaded_file is not None:
  try:
    df_loaded = load_data(uploaded_file)
    st.session_state["df"] = df_loaded
    st.success("🎉 Data uploaded successfully!")
  except Exception as e:
    st.error(f"❌ Error loading uploaded file: {e}")
elif example_dataset != "None":
  with st.spinner(f"Loading {example_dataset} dataset..."):
    try:
      if example_dataset == "Iris":
        df_loaded = sns.load_dataset("iris")
      elif example_dataset == "Tips":
        df_loaded = sns.load_dataset("tips")
      elif example_dataset == "Titanic":
        df_loaded = sns.load_dataset("titanic")
      st.session_state["df"] = df_loaded
      st.success(f"🎉 {example_dataset} dataset loaded successfully!")
    except Exception as e:
      st.error(f"❌ Error loading example dataset: {e}")

# --- Data Preview & Stats ---
if "df" in st.session_state and st.session_state["df"] is not None:
  df = st.session_state["df"]
  st.subheader("🔍 Preview of Loaded Data")
  st.dataframe(df.head(), use_container_width=True)

  st.subheader("📑 Basic Data Statistics")
  st.dataframe(df.describe(include="all").astype(str), width="stretch")
  st.markdown("---")

  st.subheader("🩺 Automated Data Health & Type Audit")

  # 1. Quick KPI Summary Row
  col1, col2, col3, col4 = st.columns(4)
  total_rows, total_cols = df.shape
  total_nulls = int(df.isnull().sum().sum())
  duplicate_rows = int(df.duplicated().sum())

  col1.metric("Total Rows", f"{total_rows:,}")
  col2.metric("Total Columns", total_cols)
  col3.metric("Missing Cells", f"{total_nulls:,}")
  col4.metric("Duplicate Rows", f"{duplicate_rows:,}")

  # 2. Column-by-Column Type, Null & Format Audit
  audit_rows = []
  for col in df.columns:
    dtype = str(df[col].dtype)
    null_count = int(df[col].isnull().sum())
    null_pct = round((null_count / len(df)) * 100, 2) if len(df) > 0 else 0
    unique_count = int(df[col].nunique(dropna=True))
    status = "✅ Clean"

    if dtype == "object":
      non_null = df[col].dropna().astype(str).str.strip()
      cleaned_num = non_null.str.replace(r"[$,]", "", regex=True)
      numeric_converted = pd.to_numeric(cleaned_num, errors="coerce")
      if len(non_null) > 0 and numeric_converted.notna().mean() > 0.8:
        if (numeric_converted.dropna() % 1 == 0).all():
          status = "⚠️ Integers stored as Object"
        else:
          status = "⚠️ Floats stored as Object"
      else:
        date_converted = pd.to_datetime(
            non_null, errors="coerce", format="mixed"
        )
        if len(non_null) > 0 and date_converted.notna().mean() > 0.8:
          status = "📅 Dates stored as Object (Not Date Format)"
    elif "datetime" in dtype:
      status = "✅ Proper Date Format"

    if null_pct > 20 and status == "✅ Clean":
      status = f"⚠️ High Nulls ({null_pct}%)"

    audit_rows.append({
        "Column": col,
        "Current Dtype": dtype,
        "Null Count": null_count,
        "Null %": f"{null_pct}%",
        "Unique Values": unique_count,
        "Diagnostic Status": status,
    })

  audit_df = pd.DataFrame(audit_rows)
  st.dataframe(audit_df, use_container_width=True)

  # 3. Interactive Data Cleaning & Analyst Tools
  st.subheader("🛠️ Analyst Quick-Fix & Export Toolkit")
  tool_tab1, tool_tab2, tool_tab3 = st.tabs([
      "🔄 Auto-Fix Data Types",
      "🧹 Handle Nulls & Duplicates",
      "📊 Correlation & Outliers",
  ])

  with tool_tab1:
    st.write(
        "Convert misformatted `object` columns into proper integers, floats, or"
        " datetime objects."
    )
    fixable_cols = audit_df[
        audit_df["Diagnostic Status"].str.contains("⚠️|📅")
    ]["Column"].tolist()
    if fixable_cols:
      selected_fix_cols = st.multiselect(
          "Select columns to auto-convert:",
          options=fixable_cols,
          default=fixable_cols,
      )
      if st.button("Apply Type Conversions"):
        df_fixed = df.copy()
        for c in selected_fix_cols:
          if c not in df_fixed.columns:
            continue
          status_msg = audit_df.loc[audit_df["Column"] == c][
              "Diagnostic Status"
          ].values[0]
          if "Integers" in status_msg or "Floats" in status_msg:
            cleaned = df_fixed[c].astype(str).str.replace(r"[$,]", "", regex=True)
            df_fixed[c] = pd.to_numeric(cleaned, errors="coerce")
            if "Integers" in status_msg:
              df_fixed[c] = df_fixed[c].astype("Int64")
          elif "Dates" in status_msg:
            df_fixed[c] = pd.to_datetime(
                df_fixed[c], errors="coerce", format="mixed"
            )
        st.session_state["df"] = df_fixed
        st.success("✅ Data types updated! Reloading audit...")
        st.rerun()
    else:
      st.info("🎉 All columns appear to be in their proper data types.")

  with tool_tab2:
    c1, c2 = st.columns(2)
    with c1:
      if st.button("Drop Duplicate Rows"):
        st.session_state["df"] = df.drop_duplicates()
        st.success(f"Removed {duplicate_rows} duplicate rows.")
        st.rerun()
    with c2:
      null_action = st.selectbox(
          "Missing Value Strategy:",
          [
              "None",
              "Drop rows with any nulls",
              "Fill numeric nulls with Mean",
              "Fill numeric nulls with Median",
              "Fill categorical nulls with Mode",
          ],
      )
      if st.button("Apply Null Fix") and null_action != "None":
        df_clean = df.copy()
        if null_action == "Drop rows with any nulls":
          df_clean = df_clean.dropna()
        elif null_action == "Fill numeric nulls with Mean":
          num_cols = df_clean.select_dtypes(include="number").columns
          df_clean[num_cols] = df_clean[num_cols].fillna(
              df_clean[num_cols].mean()
          )
        elif null_action == "Fill numeric nulls with Median":
          num_cols = df_clean.select_dtypes(include="number").columns
          df_clean[num_cols] = df_clean[num_cols].fillna(
              df_clean[num_cols].median()
          )
        elif null_action == "Fill categorical nulls with Mode":
          cat_cols = df_clean.select_dtypes(include="object").columns
          for col in cat_cols:
            if not df_clean[col].mode().empty:
              df_clean[col] = df_clean[col].fillna(df_clean[col].mode()[0])
        st.session_state["df"] = df_clean
        st.success("✅ Missing values handled!")
        st.rerun()

  with tool_tab3:
    num_df = df.select_dtypes(include="number")
    if num_df.shape[1] >= 2:
      st.write("**Numeric Correlation Matrix:**")
      st.dataframe(num_df.corr().round(2), use_container_width=True)
    else:
      st.info("Need at least 2 numeric columns to compute correlations.")

  # 4. One-Click Cleaned Dataset Download
  csv_export = st.session_state["df"].to_csv(index=False).encode("utf-8")
  st.download_button(
      label="📥 Download Cleaned Dataset (CSV)",
      data=csv_export,
      file_name="cleaned_dataset.csv",
      mime="text/csv",
  )

  # 5. Outlier Check & Clean Dataset Chart Builder
  st.markdown("---")
  st.subheader("📈 Outlier Check & Clean Dataset Visualizer")

  num_cols_check = df.select_dtypes(include="number").columns
  total_outliers = 0
  outlier_summary = {}
  for c in num_cols_check:
    q1 = df[c].quantile(0.25)
    q3 = df[c].quantile(0.75)
    iqr = q3 - q1
    out_count = int(
        ((df[c] < (q1 - 1.5 * iqr)) | (df[c] > (q3 + 1.5 * iqr))).sum()
    )
    if out_count > 0:
      outlier_summary[c] = out_count
      total_outliers += out_count

  remaining_type_issues = (
      audit_df["Diagnostic Status"].str.contains("Integers|Floats|Dates").sum()
  )

  if total_nulls == 0 and total_outliers == 0 and remaining_type_issues == 0:
    st.success(
        "🎉 Dataset is 100% clean! No null values, no outliers, and all data"
        " types are valid."
    )
    st.write("### What graph, chart, or table would you like to generate?")
    chart_choice = st.selectbox(
        "Select visualization type:",
        [
            "Bar Chart",
            "Pie Chart",
            "Line Chart",
            "Scatter Plot",
            "Histogram",
            "Filtered Rows & Columns Table",
        ],
    )

    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
      chosen_cols = st.multiselect(
          "Type or select column names:",
          options=df.columns.tolist(),
          default=df.columns.tolist()[:2]
          if len(df.columns) >= 2
          else df.columns.tolist(),
      )
    with col_sel2:
      max_r = max(0, len(df) - 1)
      start_r = st.number_input(
          "Start Row:", min_value=0, max_value=max_r, value=0
      )
      end_r = st.number_input(
          "End Row:", min_value=1, max_value=len(df), value=len(df)
      )

    if chosen_cols and start_r < end_r:
      sub_df = df[chosen_cols].iloc[start_r:end_r]
      if chart_choice == "Pie Chart":
        p_name = st.selectbox("Category Column (Names):", chosen_cols)
        p_val = st.selectbox("Value Column:", ["Row Count"] + chosen_cols)
        if p_val == "Row Count":
          counts = sub_df[p_name].value_counts().reset_index()
          counts.columns = [p_name, "Count"]
          fig = px.pie(
              counts, names=p_name, values="Count", title=f"{p_name} Breakdown"
          )
        else:
          fig = px.pie(
              sub_df, names=p_name, values=p_val, title=f"{p_val} by {p_name}"
          )
        st.plotly_chart(fig, use_container_width=True)
      elif chart_choice == "Bar Chart":
        x_c = st.selectbox("X-Axis Column:", chosen_cols)
        y_c = st.selectbox(
            "Y-Axis Column:", chosen_cols, index=min(1, len(chosen_cols) - 1)
        )
        fig = px.bar(sub_df, x=x_c, y=y_c, title=f"{y_c} vs {x_c}")
        st.plotly_chart(fig, use_container_width=True)
      elif chart_choice == "Line Chart":
        x_c = st.selectbox("X-Axis Column:", chosen_cols)
        y_c = st.selectbox(
            "Y-Axis Column:", chosen_cols, index=min(1, len(chosen_cols) - 1)
        )
        fig = px.line(sub_df, x=x_c, y=y_c, markers=True, title=f"{y_c} over {x_c}")
        st.plotly_chart(fig, use_container_width=True)
      elif chart_choice == "Scatter Plot":
        x_c = st.selectbox("X-Axis Column:", chosen_cols)
        y_c = st.selectbox(
            "Y-Axis Column:", chosen_cols, index=min(1, len(chosen_cols) - 1)
        )
        fig = px.scatter(sub_df, x=x_c, y=y_c, title=f"{y_c} vs {x_c}")
        st.plotly_chart(fig, use_container_width=True)
      elif chart_choice == "Histogram":
        h_c = st.selectbox("Column for Distribution:", chosen_cols)
        fig = px.histogram(sub_df, x=h_c, title=f"Distribution of {h_c}")
        st.plotly_chart(fig, use_container_width=True)
      elif chart_choice == "Filtered Rows & Columns Table":
        st.dataframe(sub_df, use_container_width=True)
  else:
    st.info(
        f"ℹ️ Clean all issues to unlock the Chart Builder — Remaining:"
        f" **{total_nulls} nulls**, **{total_outliers} outliers**, "
        f"**{remaining_type_issues} type mismatches**."
    )
    if total_outliers > 0 and outlier_summary:
      out_col = st.selectbox(
          "Select column with outliers to clean:", list(outlier_summary.keys())
      )
      if st.button(
          f"Remove {outlier_summary.get(out_col, 0)} Outliers from '{out_col}'"
      ):
        q1 = df[out_col].quantile(0.25)
        q3 = df[out_col].quantile(0.75)
        iqr = q3 - q1
        st.session_state["df"] = df[
            (df[out_col] >= (q1 - 1.5 * iqr)) & (df[out_col] <= (q3 + 1.5 * iqr))
        ]
        st.rerun()
else:
  st.warning(
      "⚠ Please upload a dataset or select an example dataset to get started."
  )