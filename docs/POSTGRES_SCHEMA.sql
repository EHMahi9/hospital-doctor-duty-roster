CREATE TYPE user_role AS ENUM ('super_admin', 'admin', 'doctor', 'staff');
CREATE TYPE preferred_shift AS ENUM ('morning', 'evening', 'night', 'flexible');
CREATE TYPE duty_type AS ENUM (
  'Emergency Morning',
  'Emergency Evening',
  'Emergency Night',
  'Indoor Morning',
  'Indoor Night',
  'Outdoor'
);
CREATE TYPE shift_type AS ENUM ('morning', 'evening', 'night', 'outdoor');
CREATE TYPE leave_status AS ENUM ('pending', 'approved', 'rejected');
CREATE TYPE leave_type AS ENUM ('casual', 'sick', 'earned', 'training', 'other');
CREATE TYPE notification_status AS ENUM ('pending', 'sent', 'failed');
CREATE TYPE notification_channel AS ENUM ('email', 'system');

CREATE TABLE departments (
  id SERIAL PRIMARY KEY,
  name VARCHAR(120) NOT NULL UNIQUE,
  code VARCHAR(30) NOT NULL UNIQUE,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  full_name VARCHAR(160) NOT NULL,
  hashed_password VARCHAR(255) NOT NULL,
  role user_role NOT NULL DEFAULT 'staff',
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE doctors (
  id SERIAL PRIMARY KEY,
  user_id INTEGER UNIQUE REFERENCES users(id),
  name VARCHAR(160) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  phone VARCHAR(40) NOT NULL,
  department_id INTEGER NOT NULL REFERENCES departments(id),
  designation VARCHAR(120) NOT NULL,
  max_monthly_duty INTEGER NOT NULL DEFAULT 12,
  preferred_shift preferred_shift NOT NULL DEFAULT 'flexible',
  weekly_off_day VARCHAR(12) NOT NULL DEFAULT 'Friday',
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE leave_requests (
  id SERIAL PRIMARY KEY,
  doctor_id INTEGER NOT NULL REFERENCES doctors(id),
  leave_date DATE NOT NULL,
  leave_type leave_type NOT NULL DEFAULT 'casual',
  reason TEXT NOT NULL,
  status leave_status NOT NULL DEFAULT 'pending',
  requested_by_id INTEGER REFERENCES users(id),
  reviewed_by_id INTEGER REFERENCES users(id),
  reviewed_at TIMESTAMP,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE roster_runs (
  id SERIAL PRIMARY KEY,
  month INTEGER NOT NULL,
  year INTEGER NOT NULL,
  generated_by_id INTEGER REFERENCES users(id),
  status VARCHAR(40) NOT NULL DEFAULT 'completed',
  seed INTEGER,
  summary_json JSONB,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE duty_assignments (
  id SERIAL PRIMARY KEY,
  doctor_id INTEGER NOT NULL REFERENCES doctors(id),
  duty_date DATE NOT NULL,
  duty_type duty_type NOT NULL,
  shift shift_type NOT NULL,
  roster_run_id INTEGER REFERENCES roster_runs(id),
  is_manual_override BOOLEAN NOT NULL DEFAULT FALSE,
  source VARCHAR(40) NOT NULL DEFAULT 'auto',
  notes VARCHAR(255),
  created_by_id INTEGER REFERENCES users(id),
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_doctor_one_duty_per_day UNIQUE (doctor_id, duty_date),
  CONSTRAINT uq_roster_slot_once UNIQUE (duty_date, duty_type)
);

CREATE TABLE balance_ledgers (
  id SERIAL PRIMARY KEY,
  doctor_id INTEGER NOT NULL REFERENCES doctors(id),
  month INTEGER NOT NULL,
  year INTEGER NOT NULL,
  emergency_count INTEGER NOT NULL DEFAULT 0,
  indoor_count INTEGER NOT NULL DEFAULT 0,
  outdoor_count INTEGER NOT NULL DEFAULT 0,
  night_count INTEGER NOT NULL DEFAULT 0,
  total_duties INTEGER NOT NULL DEFAULT 0,
  extra_duties INTEGER NOT NULL DEFAULT 0,
  missed_duties INTEGER NOT NULL DEFAULT 0,
  overtime_hours DOUBLE PRECISION NOT NULL DEFAULT 0,
  fairness_score DOUBLE PRECISION NOT NULL DEFAULT 100,
  workload_score DOUBLE PRECISION NOT NULL DEFAULT 0,
  updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_balance_doctor_month UNIQUE (doctor_id, month, year)
);

CREATE TABLE audit_logs (
  id SERIAL PRIMARY KEY,
  actor_id INTEGER REFERENCES users(id),
  action VARCHAR(80) NOT NULL,
  entity_type VARCHAR(80) NOT NULL,
  entity_id VARCHAR(80),
  metadata_json JSONB,
  ip_address VARCHAR(80),
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE notifications (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  title VARCHAR(160) NOT NULL,
  message TEXT NOT NULL,
  channel notification_channel NOT NULL DEFAULT 'system',
  status notification_status NOT NULL DEFAULT 'pending',
  scheduled_at TIMESTAMP,
  sent_at TIMESTAMP,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_doctors_department_id ON doctors(department_id);
CREATE INDEX ix_leave_requests_doctor_date ON leave_requests(doctor_id, leave_date);
CREATE INDEX ix_duty_assignments_month ON duty_assignments(duty_date);
CREATE INDEX ix_audit_logs_actor_created ON audit_logs(actor_id, created_at);
