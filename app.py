import io
import os
import tempfile
import streamlit as st
import fitz
from PIL import Image
from pypdf import PdfWriter
from pdf2docx import Converter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from docx import Document

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

#1. juntar pdfs
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

# 2. imagens para pdf
elif opcao == "Converter Imagem para PDF":
    imgs_upload = st.file_uploader(
        "Selecione uma ou mais imagens", 
        type=["png", "jpg", "jpeg", "webp"], 
        accept_multiple_files=True
    )
    
    if imgs_upload:
        st.write(f"**Imagens selecionadas:** {len(imgs_upload)}")
        
        # Mostra miniaturas das imagens carregadas
        cols = st.columns(min(len(imgs_upload), 4))
        for idx, img_file in enumerate(imgs_upload):
            with cols[idx % 4]:
                st.image(img_file, use_container_width=True)
                
        if st.button("Converter todas para um único PDF"):
            lista_imagens = []
            
            # Carrega e converte todas as imagens para o formato RGB
            for img_file in imgs_upload:
                img = Image.open(img_file).convert("RGB")
                lista_imagens.append(img)
            
            saida_buffer = io.BytesIO()
            
            # A primeira imagem guarda o ficheiro e anexa as restantes como páginas
            primeira_img = lista_imagens[0]
            restantes = lista_imagens[1:] if len(lista_imagens) > 1 else []
            
            primeira_img.save(
                saida_buffer, 
                format="PDF", 
                save_all=True, 
                append_images=restantes
            )
            saida_buffer.seek(0)
            
            st.success("PDF compilado com sucesso com todas as imagens!")
            st.download_button(
                "Baixar PDF Compilado", 
                saida_buffer, 
                "imagens_unidas.pdf", 
                "application/pdf"
            )


# 3. pdf para word
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

# 4. COMPRIMIR PDF
elif opcao == "Comprimir PDF":
    pdf_upload = st.file_uploader("Selecione o PDF para comprimir", type=["pdf"])
    
    nivel = st.select_slider(
        "Nível de compressão",
        options=["Leve (Melhor qualidade)", "Recomendado", "Extremo (Menor tamanho)"],
        value="Recomendado"
    )
    
    if pdf_upload:
        tamanho_original = len(pdf_upload.getvalue()) / 1024  
        st.info(f"Tamanho original: {tamanho_original:.1f} KB")
        
        if st.button("Comprimir PDF"):
            with st.spinner("Comprimindo documento..."):
                doc = fitz.open(stream=pdf_upload.read(), filetype="pdf")
                
                if nivel == "Leve (Melhor qualidade)":
                    deflate = True
                    garbage = 3
                elif nivel == "Recomendado":
                    deflate = True
                    garbage = 4
                else:  
                    deflate = True
                    garbage = 4

                saida_bytes = doc.tobytes(
                    garbage=garbage,         
                    deflate=deflate,         
                    clean=True,              
                    deflate_images=True,      
                    deflate_fonts=True        
                )
                doc.close()
                
                tamanho_novo = len(saida_bytes) / 1024  
                reducao = ((tamanho_original - tamanho_novo) / tamanho_original) * 100
                
                if tamanho_novo < tamanho_original:
                    st.success(f"PDF comprimido! Novo tamanho: {tamanho_novo:.1f} KB (Redução de {reducao:.1f}%)")
                else:
                    st.warning("Este arquivo já estava altamente otimizado e não pôde ser reduzido sem perda extrema de dados.")
                
                st.download_button(
                    "Baixar PDF Comprimido",
                    saida_bytes,
                    f"comprimido_{pdf_upload.name}",
                    "application/pdf"
                )


# 5. docx pra pdf
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
