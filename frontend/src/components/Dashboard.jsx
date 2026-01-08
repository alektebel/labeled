import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '../contexts/AuthContext'
import Navigation from './Navigation'

export default function Dashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const [tokenStats, setTokenStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      const [platformStats, userTokenStats] = await Promise.all([
        axios.get('/api/stats/platform'),
        axios.get('/api/tokens/stats')
      ])
      setStats(platformStats.data)
      setTokenStats(userTokenStats.data)
    } catch (error) {
      console.error('Failed to fetch stats:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Welcome back, {user?.username}!
          </h1>
          <p className="text-gray-600 mt-2">Earn LABD tokens by labeling data accurately</p>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="text-sm text-gray-600 mb-2">LABD Balance</div>
              <div className="text-3xl font-bold text-blue-600">
                {user?.token_balance?.toFixed(2) || '0.00'}
              </div>
              <div className="text-xs text-gray-500 mt-2">
                +{tokenStats?.total_rewards?.toFixed(2) || '0.00'} earned
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="text-sm text-gray-600 mb-2">Accuracy</div>
              <div className="text-3xl font-bold text-green-600">
                {((user?.accuracy || 0) * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-gray-500 mt-2">
                {user?.correct_labels || 0}/{user?.total_labels || 0} correct
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="text-sm text-gray-600 mb-2">Reputation</div>
              <div className="text-3xl font-bold text-purple-600">
                {((user?.reputation_score || 0) * 100).toFixed(1)}
              </div>
              <div className="text-xs text-gray-500 mt-2">
                {user?.total_labels || 0} labels submitted
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="text-sm text-gray-600 mb-2">Net Earnings</div>
              <div className={`text-3xl font-bold ${
                (tokenStats?.net_earnings || 0) >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {tokenStats?.net_earnings?.toFixed(2) || '0.00'}
              </div>
              <div className="text-xs text-gray-500 mt-2">
                Rewards - Penalties
              </div>
            </div>
          </div>
        )}

        <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-bold mb-4">Quick Actions</h2>
            <div className="space-y-3">
              <button
                onClick={() => navigate('/label')}
                className="w-full bg-blue-600 text-white py-3 rounded-md hover:bg-blue-700 transition"
              >
                Start Labeling
              </button>
              <button
                onClick={() => navigate('/leaderboard')}
                className="w-full bg-purple-600 text-white py-3 rounded-md hover:bg-purple-700 transition"
              >
                View Leaderboard
              </button>
              <button
                onClick={() => navigate('/profile')}
                className="w-full bg-gray-600 text-white py-3 rounded-md hover:bg-gray-700 transition"
              >
                View Profile
              </button>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-bold mb-4">Platform Stats</h2>
            {stats && (
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Users:</span>
                  <span className="font-bold">{stats.users}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Data Items:</span>
                  <span className="font-bold">{stats.data_items}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Labels:</span>
                  <span className="font-bold">{stats.total_labels}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Items with Consensus:</span>
                  <span className="font-bold">{stats.items_with_consensus}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Blockchain Blocks:</span>
                  <span className="font-bold">{stats.blockchain?.total_blocks}</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
