import dagshub, mlflow

dagshub.init(repo_owner='dona-eric', repo_name='air-quality', mlflow=True)
client = mlflow.MlflowClient()

# Lister les expériences
experiments = client.search_experiments()
for exp in experiments:
    print(f"Experiment: {exp.name} | ID: {exp.experiment_id}")

# Lister les runs de ton expérience
runs = client.search_runs(experiment_ids=["1"])  # adapte l'ID si besoin
for r in runs:
    print(f"Run: {r.info.run_id} | Status: {r.info.status} | Artifacts: {r.info.artifact_uri}")