import React, { useState, useEffect } from 'react';

const ProfessorDashboard = () => {
  const [courses, setCourses] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [students, setStudents] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [activeTab, setActiveTab] = useState('courses');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCourses();
    fetchAlerts();
  }, []);

  const fetchCourses = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/professor/courses');
      const data = await res.json();
      setCourses(data);
    } catch (err) {
      console.error('Failed to fetch courses:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchAlerts = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/professor/alerts');
      const data = await res.json();
      setAlerts(data);
    } catch (err) {
      console.error('Failed to fetch alerts:', err);
    }
  };

  const fetchCourseStudents = async (courseId) => {
    try {
      const res = await fetch(`http://localhost:8000/api/professor/courses/${courseId}/students`);
      const data = await res.json();
      setStudents(data);
    } catch (err) {
      console.error('Failed to fetch students:', err);
    }
  };

  const fetchCourseAnalytics = async (courseId) => {
    try {
      const res = await fetch(`http://localhost:8000/api/professor/courses/${courseId}/analytics`);
      const data = await res.json();
      setAnalytics(data);
    } catch (err) {
      console.error('Failed to fetch analytics:', err);
    }
  };

  const selectCourse = async (course) => {
    setSelectedCourse(course);
    await Promise.all([
      fetchCourseStudents(course.id),
      fetchCourseAnalytics(course.id)
    ]);
  };

  const getScoreColor = (score) => {
    if (score >= 0.7) return '#4caf50';
    if (score >= 0.4) return '#ff9800';
    return '#f44336';
  };

  if (loading) {
    return <div style={styles.loading}>Loading dashboard...</div>;
  }

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1>📊 NeuroTutor Professor Dashboard</h1>
        <span style={styles.alertBadge}>
          ⚠️ {alerts.length} At-Risk
        </span>
      </header>

      {/* Alert Banner */}
      {alerts.length > 0 && (
        <div style={styles.alertBanner}>
          <h3>🚨 At-Risk Students</h3>
          <div style={styles.alertList}>
            {alerts.slice(0, 5).map((alert, i) => (
              <div key={i} style={styles.alertItem}>
                <strong>{alert.student_name}</strong> - {alert.course_name}
                <br />
                <small>{alert.reasons.join(', ')}</small>
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={styles.main}>
        {/* Sidebar - Course List */}
        <div style={styles.sidebar}>
          <h2>My Courses</h2>
          <div style={styles.courseList}>
            {courses.map((course) => (
              <div
                key={course.id}
                style={{
                  ...styles.courseCard,
                  ...(selectedCourse?.id === course.id ? styles.courseCardActive : {})
                }}
                onClick={() => selectCourse(course)}
              >
                <div style={styles.courseCode}>{course.code}</div>
                <div style={styles.courseName}>{course.name}</div>
                <div style={styles.courseStats}>
                  <span>{course.student_count} students</span>
                  {course.at_risk_count > 0 && (
                    <span style={styles.atRiskBadge}>{course.at_risk_count} at-risk</span>
                  )}
                </div>
                <div style={styles.engagementBar}>
                  <div style={{
                    ...styles.engagementFill,
                    width: `${course.average_engagement * 100}%`,
                    backgroundColor: getScoreColor(course.average_engagement)
                  }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Main Content */}
        <div style={styles.content}>
          {selectedCourse ? (
            <>
              <div style={styles.contentHeader}>
                <h2>{selectedCourse.name}</h2>
                <div style={styles.tabs}>
                  <button
                    style={{...styles.tab, ...(activeTab === 'students' ? styles.tabActive : {})}}
                    onClick={() => setActiveTab('students')}
                  >
                    Students
                  </button>
                  <button
                    style={{...styles.tab, ...(activeTab === 'analytics' ? styles.tabActive : {})}}
                    onClick={() => setActiveTab('analytics')}
                  >
                    Analytics
                  </button>
                </div>
              </div>

              {activeTab === 'students' && (
                <div style={styles.studentTable}>
                  <table style={styles.table}>
                    <thead>
                      <tr>
                        <th>Student</th>
                        <th>Attention</th>
                        <th>Load</th>
                        <th>Engagement</th>
                        <th>Sessions</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {students.map((student) => (
                        <tr key={student.student_id} style={student.is_at_risk ? styles.atRiskRow : {}}>
                          <td>
                            <div style={styles.studentName}>{student.student_name}</div>
                            <div style={styles.studentEmail}>{student.student_email}</div>
                          </td>
                          <td>
                            <ScoreBar value={student.attention_score} />
                          </td>
                          <td>
                            <ScoreBar value={1 - student.cognitive_load} invert />
                          </td>
                          <td>
                            <ScoreBar value={student.engagement_score} />
                          </td>
                          <td>{student.sessions_count}</td>
                          <td>
                            {student.is_at_risk ? (
                              <span style={styles.statusAtRisk}>⚠️ At Risk</span>
                            ) : (
                              <span style={styles.statusGood}>✓ Healthy</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {activeTab === 'analytics' && analytics && (
                <div style={styles.analyticsGrid}>
                  <MetricCard title="Total Students" value={analytics.total_students} />
                  <MetricCard title="Active Today" value={analytics.active_students} />
                  <MetricCard title="Avg Attention" value={`${(analytics.average_attention * 100).toFixed(0)}%`} color={getScoreColor(analytics.average_attention)} />
                  <MetricCard title="Avg Engagement" value={`${(analytics.average_engagement * 100).toFixed(0)}%`} color={getScoreColor(analytics.average_engagement)} />
                  <MetricCard title="At Risk" value={analytics.at_risk_students_count} color={analytics.at_risk_students_count > 0 ? '#f44336' : '#4caf50'} />
                  <MetricCard title="Learning Hours" value={analytics.total_learning_hours} />
                  
                  <div style={styles.chartSection}>
                    <h3>Engagement Trend (7 Days)</h3>
                    <TrendChart data={analytics.engagement_trend} color="#2196f3" />
                  </div>
                  
                  <div style={styles.chartSection}>
                    <h3>Attention Trend (7 Days)</h3>
                    <TrendChart data={analytics.attention_trend} color="#4caf50" />
                  </div>
                </div>
              )}
            </>
          ) : (
            <div style={styles.placeholder}>
              <h2>Select a course to view details</h2>
              <p>Click on a course from the sidebar to see student metrics and analytics.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const ScoreBar = ({ value, invert = false }) => {
  const color = value >= 0.7 ? '#4caf50' : value >= 0.4 ? '#ff9800' : '#f44336';
  return (
    <div style={styles.scoreBar}>
      <div style={{
        ...styles.scoreFill,
        width: `${value * 100}%`,
        backgroundColor: invert ? (value >= 0.7 ? '#f44336' : value >= 0.4 ? '#ff9800' : '#4caf50') : color
      }} />
    </div>
  );
};

const MetricCard = ({ title, value, color = '#333' }) => (
  <div style={styles.metricCard}>
    <div style={styles.metricValue} style={{ color }}>{value}</div>
    <div style={styles.metricTitle}>{title}</div>
  </div>
);

const TrendChart = ({ data, color }) => (
  <div style={styles.chart}>
    {data.map((value, i) => (
      <div key={i} style={styles.chartBar}>
        <div style={{
          ...styles.chartFill,
          height: `${value * 100}%`,
          backgroundColor: color
        }} />
        <span style={styles.chartLabel}>Day {i + 1}</span>
      </div>
    ))}
  </div>
);

const styles = {
  container: {
    fontFamily: 'system-ui, sans-serif',
    backgroundColor: '#f5f7fa',
    minHeight: '100vh',
    padding: '20px'
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px',
    padding: '20px',
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
  },
  alertBadge: {
    backgroundColor: '#ffebee',
    color: '#c62828',
    padding: '8px 16px',
    borderRadius: '20px',
    fontWeight: 'bold'
  },
  alertBanner: {
    backgroundColor: '#fff3e0',
    padding: '20px',
    borderRadius: '12px',
    marginBottom: '20px',
    borderLeft: '4px solid #ff9800'
  },
  alertList: {
    display: 'flex',
    gap: '15px',
    flexWrap: 'wrap'
  },
  alertItem: {
    backgroundColor: 'white',
    padding: '12px',
    borderRadius: '8px',
    fontSize: '14px'
  },
  main: {
    display: 'grid',
    gridTemplateColumns: '300px 1fr',
    gap: '20px'
  },
  sidebar: {
    backgroundColor: 'white',
    borderRadius: '12px',
    padding: '20px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
  },
  courseList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px'
  },
  courseCard: {
    padding: '16px',
    borderRadius: '8px',
    border: '1px solid #e0e0e0',
    cursor: 'pointer',
    transition: 'all 0.2s'
  },
  courseCardActive: {
    borderColor: '#2196f3',
    backgroundColor: '#e3f2fd'
  },
  courseCode: {
    fontSize: '12px',
    color: '#666',
    fontWeight: 'bold'
  },
  courseName: {
    fontSize: '14px',
    fontWeight: '600',
    marginTop: '4px'
  },
  courseStats: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '12px',
    color: '#666',
    marginTop: '8px'
  },
  atRiskBadge: {
    color: '#f44336',
    fontWeight: 'bold'
  },
  engagementBar: {
    height: '4px',
    backgroundColor: '#e0e0e0',
    borderRadius: '2px',
    marginTop: '8px',
    overflow: 'hidden'
  },
  engagementFill: {
    height: '100%',
    borderRadius: '2px',
    transition: 'width 0.3s'
  },
  content: {
    backgroundColor: 'white',
    borderRadius: '12px',
    padding: '24px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
  },
  contentHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px'
  },
  tabs: {
    display: 'flex',
    gap: '10px'
  },
  tab: {
    padding: '8px 16px',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    backgroundColor: '#f5f5f5',
    fontSize: '14px'
  },
  tabActive: {
    backgroundColor: '#2196f3',
    color: 'white'
  },
  studentTable: {
    overflowX: 'auto'
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse'
  },
  atRiskRow: {
    backgroundColor: '#fff3e0'
  },
  studentName: {
    fontWeight: '600'
  },
  studentEmail: {
    fontSize: '12px',
    color: '#666'
  },
  scoreBar: {
    width: '100px',
    height: '8px',
    backgroundColor: '#e0e0e0',
    borderRadius: '4px',
    overflow: 'hidden'
  },
  scoreFill: {
    height: '100%',
    borderRadius: '4px'
  },
  statusAtRisk: {
    color: '#f44336',
    fontWeight: 'bold',
    fontSize: '12px'
  },
  statusGood: {
    color: '#4caf50',
    fontWeight: 'bold',
    fontSize: '12px'
  },
  analyticsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '16px'
  },
  metricCard: {
    backgroundColor: '#f5f7fa',
    padding: '20px',
    borderRadius: '8px',
    textAlign: 'center'
  },
  metricValue: {
    fontSize: '32px',
    fontWeight: 'bold'
  },
  metricTitle: {
    fontSize: '14px',
    color: '#666',
    marginTop: '4px'
  },
  chartSection: {
    gridColumn: 'span 3',
    marginTop: '20px'
  },
  chart: {
    display: 'flex',
    alignItems: 'flex-end',
    gap: '10px',
    height: '150px',
    paddingTop: '20px'
  },
  chartBar: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    height: '100%'
  },
  chartFill: {
    width: '100%',
    borderRadius: '4px 4px 0 0',
    transition: 'height 0.3s'
  },
  chartLabel: {
    fontSize: '10px',
    color: '#666',
    marginTop: '4px'
  },
  placeholder: {
    textAlign: 'center',
    padding: '60px',
    color: '#666'
  },
  loading: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100vh',
    fontSize: '18px',
    color: '#666'
  }
};

export default ProfessorDashboard;
