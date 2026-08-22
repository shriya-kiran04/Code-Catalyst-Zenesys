import { useRef, useState } from "react";
import "./App.css";

function App() {
  const [stage, setStage] = useState("upload");
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  const fileInputRef = useRef(null);

  const handleFile = (selectedFile) => {
    if (!selectedFile) return;

    const allowedTypes = [
      "application/pdf",
      "image/png",
      "image/jpeg",
    ];

    if (!allowedTypes.includes(selectedFile.type)) {
      alert("Please upload a PDF, PNG, or JPG file.");
      return;
    }

    setFile(selectedFile);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);

    const droppedFile = e.dataTransfer.files[0];
    handleFile(droppedFile);
  };

  const analyzeDocument = () => {
    if (!file) return;

    setStage("processing");

    setTimeout(() => {
      setStage("report");
    }, 2500);
  };

  return (
    <div className="app">

      {/* Background decoration */}
      <div className="background-glow glow-one"></div>
      <div className="background-glow glow-two"></div>

      {/* Navbar */}
      <nav className="navbar">

        <div className="brand">
          <div className="brand-icon">
            🛡️
          </div>

          <span>DocuSheild</span>
          <span className="brand-ai">AI</span>
        </div>

        <div className="nav-right">
          <span className="nav-link">
            How it works
          </span>

          <div className="system-status">
            <span className="status-dot"></span>
            System Ready
          </div>
        </div>

      </nav>


      {/* ================= UPLOAD ================= */}

      {stage === "upload" && (

        <main className="landing">

          <div className="hero-content">

            <div className="eyebrow">
              <span>✦</span>
              AI-POWERED DOCUMENT VERIFICATION
            </div>

            <h1>
              Trust your documents.
              <br />

              <span className="gradient-text">
                Verify with evidence.
              </span>
            </h1>

            <p className="hero-description">
              DocuSheild AI analyzes your document for
              inconsistencies, suspicious information,
              and anomalies — then lets you ask questions
              and get answers grounded directly in the document.
            </p>

          </div>


          {/* Upload card */}

          <div
            className={`upload-card ${
              dragActive ? "drag-active" : ""
            }`}
            onDragOver={(e) => {
              e.preventDefault();
              setDragActive(true);
            }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current.click()}
          >

            <input
              ref={fileInputRef}
              type="file"
              hidden
              accept=".pdf,.png,.jpg,.jpeg"
              onChange={(e) =>
                handleFile(e.target.files[0])
              }
            />

            <div className="upload-icon-wrapper">
              <div className="upload-icon">
                {file ? "✓" : "↑"}
              </div>
            </div>

            {!file ? (
              <>
                <h2>
                  Drop your document here
                </h2>

                <p>
                  or <span>browse files</span> from your computer
                </p>

                <div className="file-types">
                  <span>PDF</span>
                  <span>PNG</span>
                  <span>JPG</span>
                </div>
              </>
            ) : (
              <>
                <h2>
                  Document ready
                </h2>

                <p className="selected-file">
                  📄 {file.name}
                </p>

                <div className="file-ready">
                  ✓ Ready for analysis
                </div>
              </>
            )}

          </div>


          {/* Analyze button */}

          <button
            className={`analyze-button ${
              !file ? "disabled" : ""
            }`}
            disabled={!file}
            onClick={(e) => {
              e.stopPropagation();
              analyzeDocument();
            }}
          >
            <span>
              Analyze Document
            </span>

            <span className="button-arrow">
              →
            </span>
          </button>


          {/* Feature cards */}

          <div className="features">

            <div className="feature">
              <div className="feature-icon">
                🔍
              </div>

              <div>
                <strong>
                  Smart Analysis
                </strong>

                <p>
                  Detect inconsistencies
                </p>
              </div>
            </div>


            <div className="feature">
              <div className="feature-icon">
                🛡️
              </div>

              <div>
                <strong>
                  Evidence First
                </strong>

                <p>
                  Every finding has proof
                </p>
              </div>
            </div>


            <div className="feature">
              <div className="feature-icon">
                💬
              </div>

              <div>
                <strong>
                  Ask Your Document
                </strong>

                <p>
                  Get grounded answers
                </p>
              </div>
            </div>

          </div>

        </main>
      )}


      {/* ================= PROCESSING ================= */}

      {stage === "processing" && (

        <main className="processing-page">

          <div className="processing-orb">
            <div className="processing-ring"></div>
            <span>🛡️</span>
          </div>

          <div className="eyebrow">
            DOCUMENT ANALYSIS IN PROGRESS
          </div>

          <h1>
            Understanding your document
          </h1>

          <p>
            DocuSheild AI is extracting information,
            identifying important fields, and checking
            for inconsistencies.
          </p>

          <div className="processing-steps">

            <div className="processing-step active">
              <span>✓</span>
              Extracting document data
            </div>

            <div className="processing-step active">
              <span className="pulse-dot"></span>
              Understanding content
            </div>

            <div className="processing-step">
              <span>○</span>
              Checking for anomalies
            </div>

            <div className="processing-step">
              <span>○</span>
              Preparing verification report
            </div>

          </div>

        </main>
      )}


      {/* ================= REPORT ================= */}

      {stage === "report" && (

        <main className="report-page">

          <div className="report-header">

            <div>
              <div className="eyebrow">
                VERIFICATION COMPLETE
              </div>

              <h1>
                Verification Report
              </h1>

              <p>
                Analysis results for{" "}
                <strong>
                  {file?.name}
                </strong>
              </p>
            </div>

            <div className="risk-badge">
              ⚠ Potential Issue
            </div>

          </div>


          <div className="report-grid">

            <div className="report-main">

              <div className="issue-card">

                <div className="issue-top">

                  <div className="issue-icon">
                    ⚠
                  </div>

                  <div>
                    <span className="severity">
                      MEDIUM SEVERITY
                    </span>

                    <h2>
                      Potential Date Inconsistency
                    </h2>
                  </div>

                </div>

                <p>
                  The document contains date information
                  that requires further verification.
                </p>

                <div className="evidence-box">

                  <div className="evidence-label">
                    📄 DOCUMENT EVIDENCE
                  </div>

                  <blockquote>
                    "Invoice Date: 12/08/2026"
                  </blockquote>

                  <div className="source">
                    📍 Page 1 · Invoice Details
                  </div>

                </div>

              </div>

            </div>


            <div className="report-side">

              <div className="score-card">

                <div className="score-circle">
                  <span>72</span>
                  <small>/100</small>
                </div>

                <h3>
                  Verification Score
                </h3>

                <p>
                  Some information requires attention.
                </p>

              </div>

              <button
                className="chat-button"
                onClick={() => setStage("chat")}
              >
                💬 Ask about this document
                <span>→</span>
              </button>

            </div>

          </div>

        </main>
      )}


      {/* ================= CHAT ================= */}

      {stage === "chat" && (

        <main className="chat-page">

          <div className="chat-header">

            <div className="assistant-avatar">
              🛡️
            </div>

            <div>
              <div className="eyebrow">
                DOCUMENT GROUNDED AI
              </div>

              <h1>
                Ask your document
              </h1>

              <p>
                Answers are based only on your uploaded document.
              </p>
            </div>

          </div>


          <div className="chat-container">

            <div className="welcome-message">

              <div className="assistant-small">
                🛡️
              </div>

              <div>
                <strong>
                  DocuSheild Assistant
                </strong>

                <p>
                  Ask me anything about your uploaded
                  document. I'll provide the answer along
                  with the exact evidence used.
                </p>
              </div>

            </div>


            <div className="suggestions">

              <button>
                What is the document date?
              </button>

              <button>
                What inconsistencies were detected?
              </button>

              <button>
                Who issued this document?
              </button>

            </div>


            <div className="chat-input-wrapper">

              <input
                type="text"
                placeholder="Ask a question about your document..."
              />

              <button className="send-button">
                ↑
              </button>

            </div>

            <div className="grounded-note">
              🛡️ Answers are grounded in your uploaded document
            </div>

          </div>

        </main>
      )}

    </div>
  );
}

export default App;