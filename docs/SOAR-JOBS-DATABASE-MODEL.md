 SOAR Job Storage System Analysis & Plan

  Current State Investigation Results

  ✅ What EXISTS:
  1. Artifact Storage: save_case_artifact() function that saves files to /home/iris/server_data/cases/{case_id}/artifacts/{integration_type}/
  2. Case Notes: add_case_note() placeholder function (needs proper IRIS notes API integration)
  3. Integration Config: IntegrationConfig database model for storing API credentials
  4. Job Execution: Real SOAR job functions that make actual API calls (e.g., execute_sentinelone_fetch_apps)

  ❌ What's MISSING:
  1. No job metadata database storage - No database model to store job details, status, results
  2. Mock job details API - The /soar/jobs/<job_id> endpoint returns hardcoded mock data
  3. No job history - No way to track, retrieve, or list previous job executions
  4. No job-artifact linking - Artifacts are saved to filesystem but not linked to job records

  Proposed SOAR Job Storage System Design

  1. Database Model Design

  class SoarJob(db.Model):
      __tablename__ = 'soar_jobs'

      # Primary job metadata
      job_id = Column(String(36), primary_key=True)  # UUID
      case_id = Column(Integer, ForeignKey('cases.case_id'), nullable=False)
      template_id = Column(String(50), nullable=False)
      template_name = Column(String(200), nullable=False)
      integration_type = Column(String(50), nullable=False)  # sentinelone, velociraptor, etc.

      # Execution details
      target = Column(String(255), nullable=False)
      status = Column(String(20), nullable=False)  # Running, Completed, Failed
      executor_id = Column(Integer, ForeignKey('user.id'), nullable=False)

      # Timestamps
      created_at = Column(DateTime(timezone=True), server_default=func.now())
      started_at = Column(DateTime(timezone=True), nullable=True)
      completed_at = Column(DateTime(timezone=True), nullable=True)

      # Results and metadata
      result_data = Column(JSONB, nullable=True)  # Full job execution results
      error_message = Column(Text, nullable=True)

      # Additional job parameters
      job_parameters = Column(JSONB, nullable=True)  # Store job-specific config
      comment = Column(Text, nullable=True)

  class SoarJobStep(db.Model):
      __tablename__ = 'soar_job_steps'

      step_id = Column(String(36), primary_key=True)
      job_id = Column(String(36), ForeignKey('soar_jobs.job_id'), nullable=False)
      step_name = Column(String(200), nullable=False)
      step_order = Column(Integer, nullable=False)
      status = Column(String(20), nullable=False)
      started_at = Column(DateTime(timezone=True), nullable=True)
      completed_at = Column(DateTime(timezone=True), nullable=True)
      result_message = Column(Text, nullable=True)
      error_message = Column(Text, nullable=True)

  class SoarJobArtifact(db.Model):
      __tablename__ = 'soar_job_artifacts'

      artifact_id = Column(String(36), primary_key=True)
      job_id = Column(String(36), ForeignKey('soar_jobs.job_id'), nullable=False)
      artifact_name = Column(String(255), nullable=False)
      artifact_type = Column(String(50), nullable=False)  # json, zip, txt, etc.
      file_path = Column(String(500), nullable=False)
      file_size = Column(BigInteger, nullable=True)
      created_at = Column(DateTime(timezone=True), server_default=func.now())
      is_downloadable = Column(Boolean, default=True)

  2. Implementation Strategy

  Phase 1: Core Job Storage
  1. Create database models and migration
  2. Update job execution to store results in database
  3. Update job details API to return real data instead of mock

  Phase 2: Enhanced Features
  1. Add job history/listing endpoints
  2. Implement artifact download endpoints
  3. Integrate with IRIS notes system
  4. Add job search and filtering

  Phase 3: Advanced Features
  1. Job approval workflow
  2. Job scheduling
  3. Job templates management
  4. Performance metrics

  3. Key Benefits of This Design

  ✅ Persistent Storage: All job data survives restarts
  ✅ Audit Trail: Complete history of SOAR executions
  ✅ Artifact Management: Proper linking between jobs and files
  ✅ Case Integration: Jobs linked to cases for context
  ✅ Scalable: JSONB fields allow flexible job-specific data
  ✅ User Tracking: Know who executed what and when
  ✅ Status Monitoring: Real-time job status tracking

  4. Implementation Priority

  IMMEDIATE (Phase 1):
  - Create SoarJob database model
  - Update execute_sentinelone_fetch_apps to save job record
  - Fix /soar/jobs/<job_id> API to return real data
  - This will solve your current "mock artifacts" issue