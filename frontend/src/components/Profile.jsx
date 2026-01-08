import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { useAuth } from '../contexts/AuthContext'
import Navigation from './Navigation'

export default function Profile() {
  const { user } = useAuth()
  const [transactions, setTransactions] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchTransactions()
  }, [])

  const fetchTransactions = async () => {
    try {
      const response = await axios.get('/api/tokens/history')
      setTransactions(response.data.slice(0, 50))
    } catch (error) {
      console.error('Failed to fetch transactions:', error)
    } finally {
      setLoading(false)
    }
  }

  const getTransactionType = (tx) => {
    if (tx.transaction_type === 'reward') return 'Reward'
    if (tx.transaction_type === 'penalty') return 'Penalty'
    if (tx.transaction_type === 'mint') return 'Initial Tokens'
    if (tx.transaction_type === 'mining_reward') return 'Mining Reward'
    return 'Transfer'
  }

  const getTransactionColor = (tx) => {
    if (tx.recipient === user.wallet_address) return 'text-green-600'
    return 'text-red-600'
  }

  const getTransactionAmount = (tx) => {
    if (tx.recipient === user.wallet_address) return `+${tx.amount.toFixed(2)}`
    return `-${tx.amount.toFixed(2)}`
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Profile</h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-lg font-semibold mb-4">Account Info</h2>
            <div className="space-y-2">
              <div>
                <span className="text-gray-600 text-sm">Username:</span>
                <div className="font-bold">{user?.username}</div>
              </div>
              <div>
                <span className="text-gray-600 text-sm">Email:</span>
                <div className="font-bold">{user?.email}</div>
              </div>
              <div>
                <span className="text-gray-600 text-sm">Wallet:</span>
                <div className="font-mono text-xs break-all">{user?.wallet_address}</div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-lg font-semibold mb-4">Labeling Stats</h2>
            <div className="space-y-2">
              <div>
                <span className="text-gray-600 text-sm">Total Labels:</span>
                <div className="font-bold text-2xl">{user?.total_labels || 0}</div>
              </div>
              <div>
                <span className="text-gray-600 text-sm">Correct:</span>
                <div className="font-bold text-green-600">{user?.correct_labels || 0}</div>
              </div>
              <div>
                <span className="text-gray-600 text-sm">Incorrect:</span>
                <div className="font-bold text-red-600">{user?.incorrect_labels || 0}</div>
              </div>
              <div>
                <span className="text-gray-600 text-sm">Accuracy:</span>
                <div className="font-bold text-blue-600">
                  {((user?.accuracy || 0) * 100).toFixed(1)}%
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-lg font-semibold mb-4">Token Stats</h2>
            <div className="space-y-2">
              <div>
                <span className="text-gray-600 text-sm">Balance:</span>
                <div className="font-bold text-2xl text-blue-600">
                  {user?.token_balance?.toFixed(2) || '0.00'} LABD
                </div>
              </div>
              <div>
                <span className="text-gray-600 text-sm">Reputation:</span>
                <div className="font-bold">
                  {((user?.reputation_score || 0) * 100).toFixed(1)}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-bold">Transaction History</h2>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            </div>
          ) : transactions.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Date
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      Amount
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {transactions.map((tx, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {getTransactionType(tx)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-500">
                          {new Date(tx.timestamp * 1000).toLocaleString()}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <div className={`text-sm font-bold ${getTransactionColor(tx)}`}>
                          {getTransactionAmount(tx)} LABD
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              No transactions yet
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
