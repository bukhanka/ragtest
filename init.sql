-- Create team members table
CREATE TABLE IF NOT EXISTS team_members (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(255) NOT NULL,
    department VARCHAR(255),
    email VARCHAR(255),
    join_date DATE,
    skills TEXT[]
);

-- Insert sample data
INSERT INTO team_members (name, role, department, email, join_date, skills) VALUES
('Александр Иванов', 'Senior ML Engineer', 'Machine Learning', 'a.ivanov@company.com', '2020-03-15', ARRAY['Python', 'TensorFlow', 'PyTorch', 'NLP']),
('Мария Петрова', 'Data Scientist', 'Machine Learning', 'm.petrova@company.com', '2021-06-01', ARRAY['Python', 'Scikit-learn', 'SQL', 'Statistics']),
('Дмитрий Смирнов', 'ML Engineer', 'Machine Learning', 'd.smirnov@company.com', '2022-01-10', ARRAY['Python', 'Docker', 'MLOps', 'FastAPI']),
('Елена Васильева', 'NLP Specialist', 'Machine Learning', 'e.vasilieva@company.com', '2021-09-20', ARRAY['Python', 'NLP', 'LangChain', 'Transformers']),
('Иван Кузнецов', 'Backend Developer', 'Engineering', 'i.kuznetsov@company.com', '2020-11-05', ARRAY['Python', 'FastAPI', 'PostgreSQL', 'Redis']),
('Анна Соколова', 'DevOps Engineer', 'Engineering', 'a.sokolova@company.com', '2019-08-12', ARRAY['Docker', 'Kubernetes', 'CI/CD', 'Linux']),
('Павел Морозов', 'Team Lead', 'Machine Learning', 'p.morozov@company.com', '2018-05-20', ARRAY['Python', 'Management', 'ML', 'Architecture']),
('Ольга Новикова', 'QA Engineer', 'Quality Assurance', 'o.novikova@company.com', '2021-03-15', ARRAY['Python', 'Testing', 'Selenium', 'API Testing']);

-- Create projects table
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50),
    start_date DATE,
    end_date DATE
);

-- Insert sample projects
INSERT INTO projects (name, description, status, start_date, end_date) VALUES
('LLM Assistant', 'Разработка многофункционального LLM-ассистента', 'active', '2024-01-15', NULL),
('RAG System', 'Система поиска по документации с использованием RAG', 'active', '2024-02-01', NULL),
('SQL Agent', 'Агент для работы с SQL базами данных', 'completed', '2023-10-01', '2024-01-30');

