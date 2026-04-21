import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import AnalysisHub from './pages/AnalysisHub'
import Chat from './pages/Chat'
import History from './pages/History'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/analysis" element={<AnalysisHub />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/history" element={<History />} />
      </Route>
    </Routes>
  )
}
