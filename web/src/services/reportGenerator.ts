import jsPDF from 'jspdf'
import autoTable from 'jspdf-autotable'
import { format } from 'date-fns'

interface ReportData {
  type: 'ANALYSIS' | 'SAFETY_CHECK' | 'DIAGNOSIS'
  reportId?: string
  patient: {
    name: string
    age: number | string
    gender: string
    conditions: string[]
    medications: string[]
    allergies: string[]
  }
  findings: {
    title: string
    status?: string
    priority?: string
    content: string | string[] | any[]
    recommendation?: string
  }
  auditTrail?: {
    agent: string
    step: string
    status: string
    detail: string
  }[]
}

export const generatePDF = (data: ReportData) => {
  const doc = new jsPDF()
  const dateStr = format(new Date(), 'yyyy-MM-dd HH:mm')
  const reportId = data.reportId || `HM-2.0-${Math.random().toString(36).substr(2, 6).toUpperCase()}`

  // --- Header ---
  doc.setFillColor(108, 99, 255) // #6C63FF
  doc.rect(0, 0, 210, 40, 'F')
  
  doc.setTextColor(255, 255, 255)
  doc.setFontSize(22)
  doc.setFont('helvetica', 'bold')
  doc.text('HealthMind 2.0', 20, 25)
  
  doc.setFontSize(10)
  doc.setFont('helvetica', 'normal')
  doc.text('Dual-Agent Medical Analysis & Audit', 20, 32)
  
  doc.setFontSize(10)
  doc.text(`Report ID: ${reportId}`, 150, 15)
  doc.text(`Date: ${dateStr}`, 150, 20)

  // --- Section 1: Patient Identification ---
  doc.setTextColor(0, 0, 0)
  doc.setFontSize(14)
  doc.setFont('helvetica', 'bold')
  doc.text('PATIENT IDENTIFICATION', 20, 55)
  
  autoTable(doc, {
    startY: 60,
    head: [['Attribute', 'Details']],
    body: [
      ['Full Name', data.patient.name],
      ['Age / Gender', `${data.patient.age || 'N/A'} / ${data.patient.gender || 'N/A'}`],
      ['Conditions', data.patient.conditions.join(', ') || 'None documented'],
      ['Medications', data.patient.medications.join(', ') || 'None documented'],
      ['Allergies', data.patient.allergies.join(', ') || 'None documented'],
    ],
    theme: 'striped',
    headStyles: { fillColor: [80, 80, 80] },
    margin: { left: 20, right: 20 },
  })

  // --- Section 2: Clinical Findings ---
  const findingsStart = (doc as any).lastAutoTable.finalY + 15
  doc.setFontSize(14)
  doc.setFont('helvetica', 'bold')
  doc.text('CLINICAL ASSESSMENT', 20, findingsStart)

  doc.setFontSize(11)
  doc.setTextColor(108, 99, 255)
  doc.text(`Agent: Validation & Insight Agent`, 20, findingsStart + 8)
  
  doc.setTextColor(0, 0, 0)
  doc.setFontSize(12)
  if (data.findings.status) {
    const statusColor = data.findings.status === 'BLOCK' ? [255, 107, 107] : [255, 183, 77]
    doc.setTextColor(statusColor[0], statusColor[1], statusColor[2])
    doc.setFontSize(12)
    doc.setFont('helvetica', 'bold')
    doc.text(`STATUS: ${data.findings.status} (${data.findings.priority})`, 20, findingsStart + 18)
    doc.setTextColor(0, 0, 0)
  }

  doc.setFont('helvetica', 'normal')
  doc.setFontSize(11)
  const findingsContent = Array.isArray(data.findings.content) ? data.findings.content : [data.findings.content]
  let yIdx = findingsStart + (data.findings.status ? 25 : 18)
  
  findingsContent.forEach(item => {
    let line = typeof item === 'string' ? item : JSON.stringify(item)
    const splitText = doc.splitTextToSize(`• ${line}`, 170)
    doc.text(splitText, 20, yIdx)
    yIdx += splitText.length * 6
  })

  if (data.findings.recommendation) {
    doc.setFont('helvetica', 'bold')
    doc.text('Clinical Recommendation:', 20, yIdx + 5)
    doc.setFont('helvetica', 'normal')
    const recLines = doc.splitTextToSize(data.findings.recommendation, 170)
    doc.text(recLines, 20, yIdx + 12)
    yIdx += recLines.length * 6 + 10
  }

  // --- Section 3: Audit Trail & Reporting Agent ---
  if (data.auditTrail) {
    if (yIdx > 230) { doc.addPage(); yIdx = 20; }
    doc.setFontSize(14)
    doc.setFont('helvetica', 'bold')
    doc.text('AUDIT TRAIL & PROCESSING HISTORY', 20, yIdx + 10)
    
    doc.setFontSize(10)
    doc.setTextColor(108, 99, 255)
    doc.text(`Agent: Audit & Reporting Agent`, 20, yIdx + 16)
    
    autoTable(doc, {
      startY: yIdx + 20,
      head: [['Step', 'Agent', 'Status', 'Detail']],
      body: data.auditTrail.map(a => [a.step, a.agent, a.status, a.detail]),
      headStyles: { fillColor: [108, 99, 255] },
      margin: { left: 20, right: 20 },
      styles: { fontSize: 9 }
    })
  }

  // --- Section 4: Final Disclaimer ---
  const finalY = (doc as any).lastAutoTable?.finalY || 250
  doc.setFontSize(9)
  doc.setTextColor(100, 100, 100)
  doc.setFont('helvetica', 'italic')
  
  const disclaimer = [
    'HUMAN-IN-THE-LOOP (HITL) CERTIFICATION REQUIRED',
    'Compiled by HealthMind 2.0 Dual-Agent Processing System.',
    'Processing steps have been audited for transparency and source validation.',
    'The report is non-binding and requires licensed clinical sign-off.'
  ]
  
  doc.text(disclaimer, 20, finalY + 15)

  // --- Footer ---
  const pageCount = (doc as any).internal.getNumberOfPages()
  for (let i = 1; i <= pageCount; i++) {
    doc.setPage(i)
    doc.setFontSize(8)
    doc.text(`Page ${i} of ${pageCount} | ${reportId}`, 105, 290, { align: 'center' })
  }

  doc.save(`${reportId}_report.pdf`)
}
