from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        # Header background
        self.set_fill_color(30, 41, 59) # Slate 800
        self.rect(0, 0, 210, 40, 'F')
        
        self.set_y(15)
        self.set_font('Helvetica', 'B', 22)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, 'Sentinel-IMS: SRE Intern Assignment', 0, 1, 'C')
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f'Page {self.page_no()} | Submitted by Swarnadipta Das', 0, 0, 'C')

def create_submission_pdf():
    # Use Helvetica as a modern alternative to Arial
    pdf = PDF()
    pdf.add_page()
    
    # Candidate Info Header
    pdf.set_y(50)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(37, 99, 235) # Blue 600
    pdf.cell(0, 10, 'CANDIDATE: SWARNADIPTA DAS', 0, 1, 'C')
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 5, 'https://github.com/SwarnadiptaDas/incident-management-system', 0, 1, 'C')
    pdf.ln(10)
    
    # Mission Objective Box
    pdf.set_fill_color(248, 250, 252) # Slate 50
    pdf.set_draw_color(226, 232, 240) # Slate 200
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(30, 41, 59)
    pdf.multi_cell(190, 8, 'Mission Objective: Build a resilient, production-ready Incident Management System (IMS) designed to monitor a complex distributed stack and manage failure mediation workflows.', 1, 'L', fill=True)
    pdf.ln(10)
    
    # Pillar 1: Architecture
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 10, '1. System Architecture', 0, 1)
    pdf.set_font('Courier', '', 8)
    pdf.set_text_color(51, 65, 85)
    
    arch = """
  [ High-Volume Signals ] (10k/sec)
            |
            v
    +-------------------+      +-------------------+
    |   Sentinel API    | ---> |  Redis Ingestion  |
    |   (FastAPI/uvloop)|      |  (Buffer Queue)   |
    +-------------------+      +-------------------+
                                       |
                                       v (BRPOP)
    +-------------------+      +-------------------+
    |  Workflow Engine  | <--- |  Sentinel Worker  |
    |  (State Pattern)  |      |  (Async Logic)    |
    +-------------------+      +-------------------+
             |                         |
             v                         v
    +-------------------+      +-------------------+
    |  PostgreSQL (SoT) |      |  MongoDB (Audit)  |
    |  (Work Items/RCA) |      |  (Raw Payloads)   |
    +-------------------+      +-------------------+
    """
    pdf.multi_cell(190, 4, arch)
    pdf.ln(8)
    
    # Pillar 2: Technical Excellence
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, '2. Technical Implementation Pillars', 0, 1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(51, 65, 85)
    
    pillars = [
        ("High-Throughput Ingestion", "Utilizes Redis-backed buffering and Async Backpressure Handling to sustain bursts of 10,000 signals/sec."),
        ("Atomic Debouncing", "Strict 10s Window ensures zero incident storms while maintaining 100% data auditability."),
        ("Design Pattern Mastery", "Full implementation of State Pattern for lifecycle safety and Strategy Pattern for alerting logic."),
        ("Hybrid Data Strategy", "PostgreSQL (Transactional), MongoDB (Data Lake), and Redis (Hot-Path Aggregations)."),
        ("SRE Observability", "Deep Health Engine monitoring Postgres, Mongo, and Redis status in real-time.")
    ]
    
    for title, desc in pillars:
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(37, 99, 235)
        pdf.cell(0, 7, f"- {title}:", 0, 1)
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(51, 65, 85)
        pdf.multi_cell(180, 6, desc)
        pdf.ln(2)
    
    pdf.ln(5)
    
    # Pillar 3: Deployment
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 10, '3. Production Readiness Checklist', 0, 1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(51, 65, 85)
    pdf.multi_cell(190, 6, "The system is fully containerized with Docker Compose. Automated health checks and simulation scripts are included to verify end-to-end functionality.")
    
    pdf.output('Swarnadipta Das - Infrastructure SRE Intern Assignment.pdf')

if __name__ == "__main__":
    create_submission_pdf()
