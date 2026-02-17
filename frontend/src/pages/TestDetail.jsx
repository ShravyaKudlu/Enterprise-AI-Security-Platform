import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import {
  Box, Typography, Paper, Tabs, Tab, Grid, Card, CardContent,
  Chip, Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  LinearProgress, Alert, CircularProgress
} from '@mui/material'
import { useQuery } from 'react-query'
import { securityTestAPI } from '../api/securityTests'

function TestDetail() {
  const { testId } = useParams()
  const [activeTab, setActiveTab] = useState(0)
  const [progress, setProgress] = useState(null)

  const { data: testStatus, refetch: refetchStatus } = useQuery(
    ['testStatus', testId],
    () => securityTestAPI.getTestStatus(testId),
    { refetchInterval: 5000 }
  )

  const { data: testResults, isLoading: isLoadingResults } = useQuery(
    ['testResults', testId],
    () => securityTestAPI.getTestResults(testId)
  )

  const { data: analytics } = useQuery(
    ['testAnalytics', testId],
    () => securityTestAPI.getTestAnalytics(testId),
    { enabled: testStatus?.data?.status === 'completed' }
  )

  useEffect(() => {
    if (testStatus?.data) {
      setProgress(testStatus.data.progress)
    }
  }, [testStatus])

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue)
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'success'
      case 'running': return 'warning'
      case 'failed': return 'error'
      case 'queued': return 'info'
      default: return 'default'
    }
  }

  if (isLoadingResults) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    )
  }

  const test = testResults?.data

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Test: {test?.test_name}
      </Typography>

      {testStatus?.data?.status === 'running' && (
        <Alert severity="info" sx={{ mb: 2 }}>
          Test is currently running. Progress will update automatically.
          <LinearProgress 
            variant="determinate" 
            value={progress?.percent_complete || 0}
            sx={{ mt: 1 }}
          />
          <Typography variant="body2" sx={{ mt: 0.5 }}>
            {progress?.completed_runs || 0} / {progress?.total_runs || 0} runs completed
          </Typography>
        </Alert>
      )}

      <Paper sx={{ mb: 2 }}>
        <Tabs value={activeTab} onChange={handleTabChange}>
          <Tab label="Summary" />
          <Tab label="Results" />
          <Tab label="Findings" />
        </Tabs>

        <Box sx={{ p: 3 }}>
          {activeTab === 0 && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Test Information</Typography>
                    <Typography><strong>Status:</strong>{' '}
                      <Chip 
                        label={test?.status} 
                        color={getStatusColor(test?.status)}
                        size="small"
                      />
                    </Typography>
                    <Typography><strong>Created:</strong> {test?.created_at && new Date(test.created_at).toLocaleString()}</Typography>
                    <Typography><strong>Total Runs:</strong> {test?.total_runs}</Typography>
                    {analytics?.data && (
                      <>
                        <Typography><strong>Attack Success Rate:</strong> {analytics.data.attack_success_rate}%</Typography>
                        <Typography><strong>Leakage Incidents:</strong> {analytics.data.leakage_detected_count}</Typography>
                      </>
                    )}
                  </CardContent>
                </Card>
              </Grid>

              {analytics?.data?.risk_distribution && (
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>Risk Distribution</Typography>
                      {Object.entries(analytics.data.risk_distribution).map(([level, count]) => (
                        <Box key={level} sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography>{level}</Typography>
                          <Chip 
                            label={count} 
                            size="small"
                            color={level === 'CRITICAL' ? 'error' : level === 'HIGH' ? 'warning' : 'default'}
                          />
                        </Box>
                      ))}
                    </CardContent>
                  </Card>
                </Grid>
              )}

              {analytics?.data?.vendor_comparison && (
                <Grid item xs={12}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>Vendor Comparison</Typography>
                      <TableContainer>
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              <TableCell>Vendor</TableCell>
                              <TableCell>Runs</TableCell>
                              <TableCell>Leakage</TableCell>
                              <TableCell>Rate</TableCell>
                              <TableCell>Avg Risk</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {Object.entries(analytics.data.vendor_comparison).map(([vendor, data]) => (
                              <TableRow key={vendor}>
                                <TableCell>{vendor}</TableCell>
                                <TableCell>{data.total_runs}</TableCell>
                                <TableCell>{data.leakage_count}</TableCell>
                                <TableCell>{data.leakage_rate}%</TableCell>
                                <TableCell>{data.avg_risk_score}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    </CardContent>
                  </Card>
                </Grid>
              )}
            </Grid>
          )}

          {activeTab === 1 && (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Run ID</TableCell>
                    <TableCell>Model</TableCell>
                    <TableCell>Vendor</TableCell>
                    <TableCell>Technique</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Risk Score</TableCell>
                    <TableCell>Leakage</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {test?.runs?.map((run) => (
                    <TableRow key={run.run_id}>
                      <TableCell>{run.run_id}</TableCell>
                      <TableCell>{run.model_name}</TableCell>
                      <TableCell>{run.model_vendor}</TableCell>
                      <TableCell>{run.technique}</TableCell>
                      <TableCell>
                        <Chip 
                          label={run.status}
                          size="small"
                          color={getStatusColor(run.status)}
                        />
                      </TableCell>
                      <TableCell>
                        {run.evaluation ? (
                          <Chip 
                            label={run.evaluation.risk_score || 'N/A'}
                            size="small"
                            color={run.evaluation.risk_level === 'CRITICAL' ? 'error' : 
                                   run.evaluation.risk_level === 'HIGH' ? 'warning' : 'default'}
                          />
                        ) : 'Pending'}
                      </TableCell>
                      <TableCell>
                        {run.evaluation?.leakage_detected ? (
                          <Chip label="YES" color="error" size="small" />
                        ) : run.evaluation ? (
                          <Chip label="NO" color="success" size="small" />
                        ) : (
                          'Pending'
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}

          {activeTab === 2 && (
            <Box>
              {test?.runs?.filter(r => r.evaluation?.leakage_detected).length === 0 ? (
                <Alert severity="success">
                  No leakage detected in this test. All models properly protected data boundaries.
                </Alert>
              ) : (
                <Grid container spacing={2}>
                  {test?.runs
                    ?.filter(r => r.evaluation?.leakage_detected)
                    .map((run) => (
                      <Grid item xs={12} md={6} key={run.run_id}>
                        <Card variant="outlined">
                          <CardContent>
                            <Typography variant="h6" gutterBottom>
                              Finding #{run.run_id}
                            </Typography>
                            <Typography><strong>Model:</strong> {run.model_name}</Typography>
                            <Typography><strong>Vendor:</strong> {run.model_vendor}</Typography>
                            <Typography><strong>Technique:</strong> {run.technique}</Typography>
                            <Typography><strong>Risk Score:</strong> {run.evaluation.risk_score}</Typography>
                            <Typography><strong>Categories:</strong>{' '}
                              {run.evaluation.categories?.join(', ')}
                            </Typography>
                            <Box sx={{ mt: 2, p: 1, bgcolor: 'grey.100', borderRadius: 1 }}>
                              <Typography variant="body2" color="text.secondary">
                                Response Preview:
                              </Typography>
                              <Typography variant="body2" sx={{ mt: 0.5 }}>
                                {run.response_preview}...
                              </Typography>
                            </Box>
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                </Grid>
              )}
            </Box>
          )}
        </Box>
      </Paper>
    </Box>
  )
}

export default TestDetail