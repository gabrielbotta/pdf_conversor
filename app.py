import io
import os
import tempfile
import streamlit as st

st.set_page_config(page_title="BotaPDF", page_icon="📄", layout="centered")

st.title("📄 BotaPDF")
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
    arquivos = st.file_uploader("Selecione dois ou mais PDFs", type=["pdf"], accept_multiple_files=True)
    
    if arquivos and len(arquivos) > 1:
        if st.button("Juntar Arquivos"):
            from pypdf import PdfWriter  # Importa só ao clicar
            
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
            from PIL import Image  # Importa só ao clicar
            
            lista_imagens = [Image.open(f).convert("RGB") for f in imgs_upload]
            saida_buffer = io.BytesIO()
            
            primeira_img = lista_imagens[0]
            restantes = lista_imagens[1:] if len(lista_imagens) > 1 else []
            
            primeira_img.save(saida_buffer, format="PDF", save_all=True, append_images=restantes)
            saida_buffer.seek(0)
            
            st.success("PDF compilado com sucesso!")
            st.download_button("Baixar PDF", saida_buffer, "imagens_unidas.pdf", "application/pdf")

# ---------------------------------------------------------
# 3. PDF PARA WORD (.DOCX) - O mais pesado
# ---------------------------------------------------------
elif opcao == "Converter PDF para Word (DOCX)":
    pdf_upload = st.file_uploader("Envie o PDF para transformar em Word", type=["pdf"])
    
    if pdf_upload:
        if st.button("Converter para DOCX"):
            from pdf2docx import Converter  # Carrega apenas se for converter
            
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
# 4. COMPRIMIR PDF
# ---------------------------------------------------------
elif opcao == "Comprimir PDF":
    pdf_upload = st.file_uploader("Selecione o PDF para comprimir", type=["pdf"])
    
    modo = st.radio(
        "Tipo de Compressão:",
        ["Manter Texto Selecionável (Digital)", "Compressão Pesada / Scanner (Garantida)"],
        help="Utilize 'Compressão Pesada' para documentos digitalizados, faturas ou ficheiros que não reduzem de tamanho."
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
            import io
            
            with st.spinner("A comprimir documento..."):
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                
                if modo == "Compressão Pesada / Scanner (Garantida)":
                    doc_novo = fitz.open()
                    
                    for page in doc:
                        pix = page.get_pixmap(dpi=dpi_escolhido)
                        img_bytes = pix.tobytes("jpeg", jpg_quality=65)
                        
                        nova_pag = doc_novo.new_page(width=page.rect.width, height=page.rect.height)
                        nova_pag.insert_image(page.rect, stream=img_bytes)
                    
                    saida_bytes = doc_novo.tobytes(
                        garbage=4,
                        deflate=1,
                        use_objstms=True
                    )
                    doc_novo.close()
                    doc.close()
                else:
                    saida_bytes = doc.tobytes(
                        garbage=4,
                        deflate=1,
                        use_objstms=True,
                        clean=True
                    )
                    doc.close()
                
                tamanho_novo = len(saida_bytes) / 1024
                
                if tamanho_novo < tamanho_original:
                    reducao = ((tamanho_original - tamanho_novo) / tamanho_original) * 100
                    st.success(f"PDF comprimido! Redução de {reducao:.1f}% ({tamanho_novo:.1f} KB)")
                    arquivo_final = saida_bytes
                else:
                    st.warning("O modo digital não conseguiu reduzir este documento. Experimente a opção 'Compressão Pesada / Scanner'.")
                    arquivo_final = saida_bytes
                
                st.download_button(
                    "Baixar PDF Comprimido",
                    arquivo_final,
                    f"comprimido_{pdf_upload.name}",
                    "application/pdf"
                )
# ---------------------------------------------------------
# 5. DOCX PARA PDF
# ---------------------------------------------------------
elif opcao == "Converter DOCX para PDF":
    docx_upload = st.file_uploader("Selecione o arquivo DOCX", type=["docx"])
    
    if docx_upload:
        if st.button("Gerar PDF"):
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from docx import Document
            
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
