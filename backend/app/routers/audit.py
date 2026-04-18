def run_audit_task(job_id, file_path, protected_attr, target_col, positive_label):
    from app.database import SessionLocal
    from ml.audit import AuditEngine
    from ml.explain import ExplainEngine

    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()

        def update(progress, message):
            job.progress = progress
            job.progress_message = message
            db.commit()
            logger.info("[%s] %d%% — %s", job_id, progress, message)

        update(10, "Loading and cleaning dataset...")
        engine = AuditEngine()
        results = engine.run(
            file_path, protected_attr, target_col, positive_label,
            update_fn=update
        )
        results["job_id"] = job_id
        job.results = json.dumps(results)

        update(85, "Running explainability analysis...")
        explain_engine = ExplainEngine()
        explanation = explain_engine.run(
            engine.model, engine.X_test, engine.y_test,
            engine.X_test_raw, protected_attr, engine.groups
        )
        explanation["job_id"] = job_id
        job.explanation = json.dumps(explanation)

        update(100, "Complete")
        job.status = "complete"
        db.commit()

    except Exception as e:
        logger.error("Audit failed for job %s: %s", job_id, str(e))
        job.status = "error"
        job.progress_message = f"Error: {str(e)}"
        db.commit()
        raise
    finally:
        db.close()