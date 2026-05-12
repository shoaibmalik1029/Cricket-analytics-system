# Initial Project Report: Cricket Analytics System

## 1. Project Title
Cricket Analytics System

## 2. Project Overview
This project develops a cricket analytics platform that combines structured statistical analysis with an interactive software interface. The main goal is to support cricket understanding and decision-making through data-driven insights such as team comparison, player profiling, and match outcome prediction.

In addition to the backend analytics logic, the project includes:

- A FastAPI backend for serving analytics as JSON.
- A React frontend dashboard for interactive access to players, teams, and match prediction features.

## 3. Problem Statement
Cricket data is large, multi-dimensional, and difficult to interpret manually. Coaches, students, fans, and analysts often need fast answers to questions such as:

- Which team is stronger in a given format?
- How likely is one team to defeat another?
- Which players contribute most strongly to team performance?

The project addresses this by building an integrated system that can convert raw cricket data into usable summaries, predictions, and visual outputs.

## 4. Objectives
The main objectives of the project were:

- To build a cricket analytics engine using historical cricket data.
- To summarize player and team performance across ODI, T20I, and Test formats.
- To train a machine learning model for match outcome prediction.
- To expose the analytics engine through an API.
- To create an interactive frontend/dashboard for end users.

## 5. Tools and Technologies Used

### Programming and Data Tools
- Python
- Pandas
- NumPy
- Scikit-learn
- Joblib

### API and Interface
- FastAPI
- React
- Vite
- CSS

## 6. Project Files and Components

### Core Analytics
- `cricket.py`: Main analytics engine.
- `api.py`: FastAPI layer for exposing backend endpoints.

### Frontend
- `frontend/src/App.jsx`: Main React application for dashboard, players, teams, and predictions.
- `frontend/src/styles.css`: Styling for the frontend dashboard.
- `frontend/src/main.jsx`: Frontend entry point.

### Supporting Files
- `requirements.txt`: Python dependencies.
- `README.md`: Existing project overview.

## 7. Methodology and Steps Performed

### Step 1: Understanding the Data
The analytics engine uses structured cricket datasets for:

- Player innings statistics
- Team batting statistics
- Team bowling statistics
- Team match results

The current implementation is organized around three match formats:

- ODI
- T20I
- Test

The data source paths are defined in `cricket.py`, and multiple historical CSV files are loaded for each format.

### Step 2: Data Cleaning and Standardization
Several preprocessing functions were implemented in `cricket.py` to make the data usable:

- Cleaning text fields
- Normalizing names
- Converting values to numeric format
- Converting overs into balls
- Parsing opposition and match text
- Safely handling missing values

This step ensures that different source files can be merged into a consistent analysis workflow.

### Step 3: Data Loading and Integration
The `CricketAnalyticsEngine` class loads all source files and combines them into unified DataFrames:

- `player_innings`
- `team_batting`
- `team_bowling`
- `team_results`

The engine also generates a dataset summary including:

- Formats covered
- Total player rows
- Total result rows
- Number of unique players
- Number of teams
- Date range of records

### Step 4: Caching for Performance
To avoid reprocessing the complete dataset every time, the system uses a cache directory:

- `.cricket_cache`

Processed tables are saved as parquet files, while the trained model and metadata are saved using Joblib. This improves startup speed and makes the application more practical for repeated use.

### Step 5: Feature Engineering
The analytics engine computes derived performance features for players and teams.

For players, the system calculates:

- Runs, outs, wickets
- Batting average
- Strike rate
- Bowling average
- Economy rate
- Bowling strike rate
- Boundary percentage
- Batting impact
- Bowling impact
- All-round impact
- Role inference such as batter, bowler, all-rounder, or utility

For teams, the system calculates:

- Matches played
- Wins and losses
- Win rate
- Loss rate
- Batting averages
- Batting runs per over
- Bowling averages
- Bowling runs per over

The model also derives matchup-oriented features such as:

- Head-to-head win rate
- Home/away or neutral condition encoding
- Opponent strength features
- Match year

### Step 6: Machine Learning Model Training
The match prediction model is implemented in `cricket.py` using `RandomForestClassifier`.

Current model configuration:

- Algorithm: Random Forest Classifier
- Number of trees: 220
- Maximum depth: 14
- Random state: 42
- Parallel training: enabled with `n_jobs=-1`

The target variable is whether the selected team won the match (`won_flag`).

Input features include:

- Match format
- Team identity
- Opponent identity
- Venue mode
- Year
- Team strength indicators
- Opponent strength indicators
- Head-to-head win rate

### Step 7: Prediction and Reporting Functions
The engine supports several end-user analytical functions:

- Match prediction
- Team searching
- Player searching
- Team profile generation
- Player profile generation

Example prediction output includes:

- Predicted winner
- Win probability for both teams
- Head-to-head rate
- Strength metrics for both teams

### Step 8: Backend API Development
The project exposes the analytics engine through FastAPI endpoints in `api.py`.

Available endpoint groups include:

- `/health`
- `/meta`
- `/dashboard`
- `/predict/options`
- `/predict`
- `/teams`
- `/teams/{team_name}`
- `/players`
- `/players/{player_name}`

This allows the frontend and other tools to query the analytics engine through HTTP.

### Step 9: Frontend Dashboard Development
The React frontend in `frontend/src/App.jsx` was built to provide a more user-friendly interface than command-line access.

The frontend contains the following sections:

- Dashboard
- Predictions
- Players
- Teams
- Settings

It displays:

- Dataset summary information
- Top teams
- Top batters
- Top bowlers
- Prediction controls and outputs
- Player and team profile tables

The design uses a professional dashboard layout with responsive CSS in `frontend/src/styles.css`.

## 8. Current Results Verified from the Repository

### Analytics Engine Results
Running the current Python analytics engine confirms the following summary:

- Formats supported: ODI, T20I, Test
- Total player innings rows: 834,900
- Total result rows: 14,991
- Total unique players: 3,933
- Total teams: 17
- Date range: 1877-03-15 to 2020-04-12

### Sample Prediction Result
A verified sample prediction from the live engine for ODI India vs Australia produced:

- Predicted winner: India
- India win probability: 55.76%
- Australia win probability: 44.24%
- Historical head-to-head rate for India in that matchup: 35.86%

Strength metrics used in that prediction included team batting, bowling, and win-rate features.

### Frontend/API Status
The repository includes a working FastAPI service layer and a React frontend structured to consume it. The frontend is designed to present:

- Top teams
- Top batters
- Top bowlers
- Match prediction forms
- Player profiles
- Team profiles

## 9. Key Achievements
- Built a reusable cricket analytics engine covering three international formats.
- Implemented structured cleaning, aggregation, and feature engineering logic.
- Trained a Random Forest match prediction model.
- Exposed the system through a FastAPI backend.
- Built a React-based interactive dashboard.
- Added caching to improve repeated execution performance.

## 10. Limitations
The current initial version also has some important limitations:

- The analytics engine depends on a hard-coded local dataset path in `cricket.py`, which reduces portability.
- No formal automated evaluation report for model accuracy is generated by the current engine code itself.
- The older `README.md` appears to describe a different or earlier dataset configuration, so documentation and current code are not fully aligned.
- The frontend contains a placeholder global search input that is not yet connected to backend search behavior.

## 11. Conclusion
This project successfully establishes an initial end-to-end cricket analytics platform with data ingestion, feature engineering, machine learning prediction, API exposure, and interactive frontend presentation.

The current version is a strong foundation for a larger intelligent cricket analysis platform. The analytics portion is already functional and verifiable, and it provides a practical base for future enhancement.

## 12. Future Work
Recommended next improvements are:

- Replace hard-coded dataset paths with configurable environment or relative paths.
- Add model evaluation reporting such as train/test metrics and confusion matrix outputs.
- Connect the frontend search bar to backend queries.
- Add exportable PDF or dashboard report generation.
- Extend the prediction engine with more contextual features such as venue history and recent form.
- Add automated tests for API responses and model workflows.

## 13. Submission Note
This report is an initial project report based on the current repository contents, implementation structure, and directly verified runtime outputs available in the workspace on May 3, 2026.
