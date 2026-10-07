import io
import os
import tempfile
import streamlit as st
from PIL import Image
from pypdf import PdfWriter
from pdf2docx import Converter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from docx import Document

st.set_page_config(page_title="Canivete Suíço de PDF", page_icon="📄", layout="centered")

st.title("📄 Mini iLovePDF")
st.write("Converta, junte e comprima arquivos diretamente no navegador.")

opcao = st.selectbox(
    "Escolha uma operação:",
    [
        "Juntar múltiplos PDFs",
        "Converter Imagem para PDF",
        "Converter PDF para Word (DOCX)",
        "Comprimir PDF",
        "Converter DOCX para PDF",
    ]
)

st.divider()

# ---------------------------------------------------------
# 1. JUNTAR PDFs (usando PdfWriter nativo)
# ---------------------------------------------------------
if opcao == "Juntar múltiplos PDFs":
    arquivos = st.file_uploader("Selecione dois ou mais arquivos PDF", type=["pdf"], accept_multiple_files=True)
    
    if arquivos and len(arquivos) > 1:
        if st.button("Juntar Arquivos"):
            writer = PdfWriter()
            for arq in arquivos:
                writer.append(arq)
            
            saida_buffer = io.BytesIO()
            writer.write(saida_buffer)
            writer.close()
            saida_buffer.seek(0)
            
            st.success("PDFs combinados com sucesso!")
            st.download_button("Baixar PDF Unido", saida_buffer, "documento_unido.pdf", "application/pdf")

# ---------------------------------------------------------
# 2. IMAGEM PARA PDF
# ---------------------------------------------------------
elif opcao == "Converter Imagem para PDF":
    img_upload = st.file_uploader("Selecione a imagem", type=["png", "jpg", "jpeg", "webp"])
    
    if img_upload:
        st.image(img_upload, caption="Pré-visualização", use_container_width=True)
        if st.button("Converter para PDF"):
            img = Image.open(img_upload).convert("RGB")
            saida_buffer = io.BytesIO()
            img.save(saida_buffer, format="PDF")
            saida_buffer.seek(0)
            
            st.success("Imagem convertida!")
            st.download_button("Baixar PDF", saida_buffer, f"{img_upload.name.rsplit('.', 1)[0]}.pdf", "application/pdf")

# ---------------------------------------------------------
# 3. PDF PARA WORD (.DOCX)
# ---------------------------------------------------------
elif opcao == "Converter PDF para Word (DOCX)":
    pdf_upload = st.file_uploader("Envie o PDF para transformar em Word", type=["pdf"])
    
    if pdf_upload:
        if st.button("Converter para DOCX"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                temp_pdf.write(pdf_upload.read())
                temp_pdf_path = temp_pdf.name
            
            docx_path = temp_pdf_path.replace(".pdf", ".docx")
            
            with st.spinner("Processando layout e texto..."):
                cv = Converter(temp_pdf_path)
                cv.convert(docx_path)
                cv.close()
                
                with open(docx_path, "rb") as f:
                    dados_docx = f.read()
            
            os.remove(temp_pdf_path)
            os.remove(docx_path)
            
            st.success("Arquivo Word gerado com sucesso!")
            st.download_button("Baixar Word (.docx)", dados_docx, f"{pdf_upload.name.rsplit('.', 1)[0]}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

# ---------------------------------------------------------
# 4. COMPRIMIR PDF
# ---------------------------------------------------------
elif opcao == "Comprimir PDF":
    pdf_upload = st.file_uploader("Selecione o PDF para comprimir", type=["pdf"])
    qualidade = st.slider("Qualidade das imagens embutidas (%)", min_value=30, max_value=90, value=65)
    
    if pdf_upload:
        if st.button("Comprimir"):
            writer = PdfWriter(clone_from=pdf_upload)
            for page in writer.pages:
                page.compress_content_streams()
                for img in page.images:
                    img.replace(img.image, quality=qualidade)
            
            saida_buffer = io.BytesIO()
            writer.write(saida_buffer)
            saida_buffer.seek(0)
            
            st.success("PDF comprimido!")
            st.download_button("Baixar PDF Comprimido", saida_buffer, f"comprimido_{pdf_upload.name}", "application/pdf")

# ---------------------------------------------------------
# 5. DOCX PARA PDF
# ---------------------------------------------------------
elif opcao == "Converter DOCX para PDF":
    docx_upload = st.file_uploader("Selecione o arquivo DOCX", type=["docx"])
    
    if docx_upload:
        if st.button("Gerar PDF"):
            doc = Document(docx_upload)
            saida_buffer = io.BytesIO()
            c = canvas.Canvas(saida_buffer, pagesize=letter)
            largura, altura = letter
            y = altura - 50
            
            for p in doc.paragraphs:
                txt = p.text.strip()
                if txt:
                    c.drawString(50, y, txt)
                    y -= 18
                    if y < 50:
                        c.showPage()
                        y = altura - 50
            c.save()
            saida_buffer.seek(0)
            
            st.success("PDF gerado!")
            
            st.download_button("Baixar PDF", saida_buffer, f"{docx_upload.name.rsplit('.', 1)[0]}.pdf", "application/pdf")