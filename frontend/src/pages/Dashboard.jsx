import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box, Typography, Grid, Paper, Card, CardContent,
  Button, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Chip, CircularProgress
} from '@mui/material'
import { useQuery } from 'react-query'
import { securityTestAPI } from '../api/securityTests'

function Dashboard() {
  const navigate = useNavigate()
  const [vendorStats, setVendorStats] = useState([])

  const { data: vendorComparison, isLoading: isLoadingVendors } = useQuery(
    'vendorComparison',
    () => securityTestAPI.getVendorComparison(),
    { refetchInterval: 30000 }
  )

  const { data: complianceData, isLoading: isLoadingCompliance } = useQuery(
    'compliance',
    () => securityTestAPI.getComplianceDashboard()
  )

  useEffect(() => {
    if (vendorComparison?.data?.vendors) {
      setVendorStats(vendorComparison.data.vendors)
    }
  }, [vendorComparison])

  const getRiskColor = (rate) => {
    if (rate <= 10) return 'success'
    if (rate <= 30) return 'warning'
    if (rate <= 50) return 'error'
    return 'error'
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Security Dashboard
      </Typography>

      <Grid container spacing={3}>
        {/* KPI Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6">Tests Run</Typography>
            <Typography variant="h3">{vendorStats.length > 0 ? '12' : '0'}</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6">Vulnerabilities</Typography>
            <Typography variant="h3" color="error">
              {vendorStats.reduce((acc, v) => acc + (v.leakage_incidents || 0), 0)}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6">Avg Risk Score</Typography>
            <Typography variant="h3">
              {vendorStats.length > 0 
                ? (vendorStats.reduce((acc, v) => acc + (v.avg_risk_score || 0), 0) / vendorStats.length).toFixed(1)
                : '0.0'}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6">Compliance Status</Typography>
            <Chip 
              label={complianceData?.data ? "Review Required" : "Pending"} 
              color={complianceData?.data ? "warning" : "default"}
            />
          </Paper>
        </Grid>

        {/* Vendor Comparison */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Vendor Vulnerability Comparison
            </Typography>
            {isLoadingVendors ? (
              <CircularProgress />
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Vendor</TableCell>
                      <TableCell>Total Runs</TableCell>
                      <TableCell>Leakage Incidents</TableCell>
                      <TableCell>Leakage Rate</TableCell>
                      <TableCell>Avg Risk Score</TableCell>
                      <TableCell>Max Risk Score</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {vendorStats.map((vendor) => (
                      <TableRow key={vendor.vendor}>
                        <TableCell>{vendor.vendor}</TableCell>
                        <TableCell>{vendor.total_runs}</TableCell>
                        <TableCell>{vendor.leakage_incidents}</TableCell>
                        <TableCell>
                          <Chip 
                            label={`${vendor.leakage_rate}%`}
                            color={getRiskColor(vendor.leakage_rate)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{vendor.avg_risk_score}</TableCell>
                        <TableCell>{vendor.max_risk_score}</TableCell>
                      </TableRow>
                    ))}
                    {vendorStats.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={6} align="center">
                          No data available. Run a security test to see results.
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Paper>
        </Grid>

        {/* Compliance Impact */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Compliance Impact
            </Typography>
            {isLoadingCompliance ? (
              <CircularProgress />
            ) : complianceData?.data ? (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Framework</TableCell>
                      <TableCell>Violations</TableCell>
                      <TableCell>Risk Level</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {Object.entries(complianceData.data).map(([framework, data]) => (
                      <TableRow key={framework}>
                        <TableCell>{framework}</TableCell>
                        <TableCell>{data.violation_count}</TableCell>
                        <TableCell>
                          <Chip 
                            label={data.overall_risk_level}
                            color={data.overall_risk_level === 'HIGH' ? 'error' : 
                                   data.overall_risk_level === 'MEDIUM' ? 'warning' : 'success'}
                            size="small"
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
              <Typography>No compliance data available</Typography>
            )}
          </Paper>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Button 
                variant="contained" 
                onClick={() => navigate('/test/new')}
              >
                Run New Test
              </Button>
              <Button variant="outlined">
                Export Report
              </Button>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}

export default Dashboard