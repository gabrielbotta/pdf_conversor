import io
import os
import tempfile
import textwrap
import streamlit as st

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
# 1. JUNTAR PDFs
# ---------------------------------------------------------
if opcao == "Juntar múltiplos PDFs":
    arquivos = st.file_uploader("Selecione dois ou mais arquivos PDF", type=["pdf"], accept_multiple_files=True)
    
    if arquivos and len(arquivos) > 1:
        if st.button("Juntar Arquivos"):
            from pypdf import PdfWriter
            
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
# 2. CONVERTER IMAGENS PARA PDF (ÚNICA OU MÚLTIPLAS)
# ---------------------------------------------------------
elif opcao == "Converter Imagem para PDF":
    imgs_upload = st.file_uploader(
        "Selecione uma ou mais imagens", 
        type=["png", "jpg", "jpeg", "webp"], 
        accept_multiple_files=True
    )
    
    if imgs_upload:
        st.write(f"**Imagens selecionadas:** {len(imgs_upload)}")
        cols = st.columns(min(len(imgs_upload), 4))
        for idx, img_file in enumerate(imgs_upload):
            with cols[idx % 4]:
                st.image(img_file, use_container_width=True)
                
        if st.button("Converter todas para um único PDF"):
            from PIL import Image
            
            lista_imagens = [Image.open(f).convert("RGB") for f in imgs_upload]
            saida_buffer = io.BytesIO()
            
            primeira_img = lista_imagens[0]
            restantes = lista_imagens[1:] if len(lista_imagens) > 1 else []
            
            primeira_img.save(saida_buffer, format="PDF", save_all=True, append_images=restantes)
            saida_buffer.seek(0)
            
            st.success("PDF compilado com sucesso!")
            st.download_button("Baixar PDF", saida_buffer, "imagens_unidas.pdf", "application/pdf")

# ---------------------------------------------------------
# 3. PDF PARA WORD (.DOCX)
# ---------------------------------------------------------
elif opcao == "Converter PDF para Word (DOCX)":
    pdf_upload = st.file_uploader("Envie o PDF para transformar em Word", type=["pdf"])
    
    if pdf_upload:
        if st.button("Converter para DOCX"):
            from pdf2docx import Converter
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                temp_pdf.write(pdf_upload.getvalue())
                temp_pdf_path = temp_pdf.name
            
            docx_path = temp_pdf_path.replace(".pdf", ".docx")
            
            with st.spinner("Processando layout e texto..."):
                cv = Converter(temp_pdf_path)
                cv.convert(docx_path)
                cv.close()
                
                with open(docx_path, "rb") as f:
                    dados_docx = f.read()
            
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)
            if os.path.exists(docx_path):
                os.remove(docx_path)
            
            st.success("Arquivo Word gerado com sucesso!")
            st.download_button(
                "Baixar Word (.docx)", 
                dados_docx, 
                f"{pdf_upload.name.rsplit('.', 1)[0]}.docx", 
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

# ---------------------------------------------------------
# 4. COMPRIMIR PDF (PyMuPDF - Digital ou Scanner)
# ---------------------------------------------------------
elif opcao == "Comprimir PDF":
    pdf_upload = st.file_uploader("Selecione o PDF para comprimir", type=["pdf"])
    
    modo = st.radio(
        "Tipo de Compressão:",
        ["Manter Texto Selecionável (Digital)", "Compressão Pesada / Scanner (Garantida)"],
        help="Use 'Compressão Pesada' para documentos digitalizados ou arquivos que insistem em ficar grandes."
    )
    
    if modo == "Compressão Pesada / Scanner (Garantida)":
        dpi_escolhido = st.select_slider(
            "Resolução visual:",
            options=[72, 100, 150],
            value=100,
            format_func=lambda x: f"{x} DPI (Leve)" if x == 72 else (f"{x} DPI (Equilibrado)" if x == 100 else f"{x} DPI (Mais nítido)")
        )
    
    if pdf_upload:
        pdf_bytes = pdf_upload.getvalue()
        tamanho_original = len(pdf_bytes) / 1024
        st.info(f"Tamanho original: {tamanho_original:.1f} KB")
        
        if st.button("Comprimir PDF"):
            import fitz
            
            with st.spinner("Comprimindo documento..."):
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                
                if modo == "Compressão Pesada / Scanner (Garantida)":
                    doc_novo = fitz.open()
                    
                    for page in doc:
                        pix = page.get_pixmap(dpi=dpi_escolhido)
                        img_bytes = pix.tobytes("jpeg", jpg_quality=65)
                        
                        nova_pag = doc_novo.new_page(width=page.rect.width, height=page.rect.height)
                        nova_pag.insert_image(page.rect, stream=img_bytes)
                    
                    saida_bytes = doc_novo.tobytes(garbage=4, deflate=1, use_objstms=True)
                    doc_novo.close()
                    doc.close()
                else:
                    saida_bytes = doc.tobytes(garbage=4, deflate=1, use_objstms=True, clean=True)
                    doc.close()
                
                tamanho_novo = len(saida_bytes) / 1024
                
                if tamanho_novo < tamanho_original:
                    reducao = ((tamanho_original - tamanho_novo) / tamanho_original) * 100
                    st.success(f"PDF comprimido! Redução de {reducao:.1f}% ({tamanho_novo:.1f} KB)")
                else:
                    st.warning("O modo digital não reduziu este documento. Experimente 'Compressão Pesada / Scanner'.")
                
                st.download_button(
                    "Baixar PDF Comprimido",
                    saida_bytes,
                    f"comprimido_{pdf_upload.name}",
                    "application/pdf"
                )

# ---------------------------------------------------------
# 5. CONVERTER DOCX PARA PDF (ÚNICO OU MÚLTIPLOS EM UM PDF)
# ---------------------------------------------------------
elif opcao == "Converter DOCX para PDF":
    docxs_upload = st.file_uploader(
        "Selecione um ou mais arquivos DOCX", 
        type=["docx"], 
        accept_multiple_files=True
    )
    
    if docxs_upload:
        st.write(f"**Documentos selecionados:** {len(docxs_upload)}")
        
        if st.button("Converter para PDF"):
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from docx import Document
            
            saida_buffer = io.BytesIO()
            c = canvas.Canvas(saida_buffer, pagesize=letter)
            largura, altura = letter
            
            for idx, docx_file in enumerate(docxs_upload):
                # Inicia cada novo documento DOCX em uma nova página (a partir do 2º)
                if idx > 0:
                    c.showPage()
                
                y = altura - 50
                doc = Document(docx_file)
                
                for p in doc.paragraphs:
                    txt = p.text.strip()
                    if txt:
                        # Quebra linhas longas para não cortarem na margem direita da folha
                        linhas = textwrap.wrap(txt, width=85)
                        for linha in linhas:
                            c.drawString(50, y, linha)
                            y -= 16
                            if y < 50:
                                c.showPage()
                                y = altura - 50
                        y -= 6  # Pequeno espaço extra entre parágrafos
            
            c.save()
            saida_buffer.seek(0)
            
            nome_saida = "documentos_unidos.pdf" if len(docxs_upload) > 1 else f"{docxs_upload[0].name.rsplit('.', 1)[0]}.pdf"
            
            st.success("PDF gerado com sucesso!")
            st.download_button("Baixar PDF", saida_buffer, nome_saida, "application/pdf")
