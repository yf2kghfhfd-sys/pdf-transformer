<p>Upload a disordered answer key or raw solutions PDF to safely compile it into a beautifully sorted layout format.</p>
            
            <form id="uploadForm">
                <div class="upload-box" onclick="document.getElementById('fileInput').click()">
                    <input type="file" id="fileInput" name="file" accept=".pdf" style="display:none;">
                    <span id="fileNameDisplay">Drag & drop or Click to choose your solution PDF</span>
                </div>
                <button type="submit">Rearrange & Download Exam Format</button>
            </form>
            <div id="status"></div>
        </div>

        <script>
            const fileInput = document.getElementById('fileInput');
            const fileDisplay = document.getElementById('fileNameDisplay');
            
            fileInput.addEventListener('change', (e) => {
                if(e.target.files.length > 0) {
                    fileDisplay.innerText = "Selected: " + e.target.files[0].name;
                }
            });

            document.getElementById('uploadForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                if(!fileInput.files[0]) return alert("Please select a file first.");

                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                
                const statusDiv = document.getElementById('status');
                statusDiv.innerText = "Extracting details, normalizing variables, and arranging layout sheets...";

                try {
                    const response = await fetch('/reformat', {
                        method: 'POST',
                        body: formData
                    });

                    if (response.ok) {
                        statusDiv.innerText = "Success! Starting download...";
                        const blob = await response.blob();
                        const downloadUrl = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = downloadUrl;
                        a.download = "Formatted_Exam_Booklet.pdf";
                        document.body.appendChild(a);
                        a.click();
                        a.remove();
                    } else {
                        const err = await response.json();
                        statusDiv.innerText = "Error encountered: " + err.error;
                    }
                } catch (e) {
                    statusDiv.innerText = "Failed to process document configuration.";
                }
            });
        </script>
    </body>
    </html>
    """

@app.route('/reformat', methods=['POST'])
def handle_reformat():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    uploaded_file = request.files['file']
    if uploaded_file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    try:
        # Step 1: Programmatically digest unstructured sections
        header_title, questions = parse_disordered_pdf(uploaded_file)
        
        # Step 2: Set up a local scratch path for rendering the clean engine asset
        temp_output_path = "generated_output.pdf"
        
        # Step 3: Run ReportLab asset mapping compilation
        build_sorted_pdf(temp_output_path, header_title, questions)
        
        # Step 4: Stream down final compiled vector graphics to the user machine
        return send_file(temp_output_path, as_attachment=True, download_name="Normalized_Exam.pdf")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if name == 'main':
    app.run(debug=True)