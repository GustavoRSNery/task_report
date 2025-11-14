// Espera o HTML ser totalmente carregado
document.addEventListener('DOMContentLoaded', function() {

    // --- Bloco 1: WebSocket e Lógica do Botão (Não muda) ---
    // ... (O código do WebSocket não precisa de NENHUMA alteração) ...
    const statusMessageEl = document.getElementById('status-message');
    const runButton = document.getElementById('run-button');
    const statusBox = document.getElementById('status-box');
    const pageLoader = document.getElementById('page-loader');
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${wsProtocol}//${window.location.host}/ws`);
    ws.onmessage = function(event) {
        const message = event.data;
        if (pageLoader.style.display !== 'none') { pageLoader.style.display = 'none'; }
        if (message.startsWith('Passo') || message.startsWith('Salvando') || message.startsWith('Erro')) { statusBox.style.display = 'block'; }
        statusMessageEl.innerText = message;
        if (message !== 'Idle' && !message.startsWith('Erro')) { runButton.disabled = true; runButton.innerText = 'Rodando...'; } 
        else { runButton.disabled = false; runButton.innerText = 'Rodar Extração Agora'; }
    };
    ws.onopen = function(event) { console.log("WebSocket conectado."); };
    ws.onclose = function(event) { console.log("WebSocket desconectado."); statusBox.style.display = 'block'; statusMessageEl.innerText = "Desconectado"; runButton.disabled = true; };
    ws.onerror = function(event) { console.error("Erro no WebSocket:", event); statusBox.style.display = 'block'; statusMessageEl.innerText = "Erro de conexão"; };
    runButton.addEventListener('click', async function() {
        pageLoader.style.display = 'flex';
        runButton.disabled = true;
        runButton.innerText = 'Iniciando...';
        try { const response = await fetch('/run-extraction', { method: 'POST' }); if (!response.ok) { throw new Error(`Servidor respondeu ${response.status}`); } } 
        catch (err) { console.error("Erro ao rodar extração:", err); pageLoader.style.display = 'none'; statusBox.style.display = 'block'; statusMessageEl.innerText = "Erro ao conectar."; runButton.disabled = false; runButton.innerText = 'Rodar Extração Agora'; }
    });


    // --- Bloco 2, 3, 4: A GRANDE RECONCILIAÇÃO ---

    const table = document.querySelector('table');
    const tableContainer = document.getElementById('table-container');
    const dataRows = document.querySelectorAll('tbody tr');
    const filterSelects = document.querySelectorAll('#filter-row select');
    const toggleBtn = document.getElementById('toggle-columns-btn');
    const toggleMenu = document.getElementById('column-toggles');
    const toggleCheckboxes = toggleMenu.querySelectorAll('input[type="checkbox"]');

    // --- Bloco 2: Lógica de Redimensionamento (Atualizada) ---
    let currentResizer;
    let startX;
    let startColumnWidth;
    let startTableWidth;

    table.querySelectorAll('thead tr:first-child th').forEach(function(header) {
        // Salva a largura inicial no 'data-' para podermos recuperá-la
        header.setAttribute('data-last-width', header.style.width || (header.offsetWidth + 'px'));
        
        const resizer = document.createElement('div');
        resizer.classList.add('resizer');
        header.appendChild(resizer);
        resizer.addEventListener('mousedown', onMouseDown);
    });

    function onMouseDown(e) {
        e.stopPropagation(); 
        currentResizer = e.target;
        startX = e.pageX;
        startColumnWidth = currentResizer.parentElement.offsetWidth;
        startTableWidth = table.offsetWidth;
        
        tableContainer.style.userSelect = 'none';
        tableContainer.style.cursor = 'col-resize';

        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
    }

    function onMouseMove(e) {
        if (!currentResizer) return;
        const moveX = e.pageX - startX;
        const newColumnWidth = startColumnWidth + moveX;
        const newTableWidth = startTableWidth + moveX;

        if (newColumnWidth > 50) { // Largura mínima
            const th = currentResizer.parentElement;
            
            // Aplica a nova largura
            th.style.width = newColumnWidth + 'px';
            
            // Salva a nova largura para a lógica de "Ocultar"
            th.setAttribute('data-last-width', newColumnWidth + 'px'); 
            
            // Atualiza a largura total da tabela
            table.style.width = newTableWidth + 'px';
        }
    }

    function onMouseUp() {
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
        
        tableContainer.style.userSelect = '';
        tableContainer.style.cursor = '';
        currentResizer = null;
    }

    // --- Bloco 3: Lógica para Popular Filtros (Atualizada) ---
    const uniqueColumnValues = {};
    filterSelects.forEach(select => {
        const colClass = select.getAttribute('data-col');
        uniqueColumnValues[colClass] = new Set();
    });

    dataRows.forEach(row => {
        const cells = row.querySelectorAll('td');
        cells.forEach(cell => {
            const colClass = cell.classList[0];
            if (uniqueColumnValues[colClass]) {
                uniqueColumnValues[colClass].add(cell.textContent.trim());
            }
        });
    });

    filterSelects.forEach(select => {
        const colClass = select.getAttribute('data-col');
        const options = uniqueColumnValues[colClass];
        const sortedOptions = Array.from(options).sort();
        sortedOptions.forEach(value => {
            if (value === "") return;
            const option = document.createElement('option');
            option.value = value;
            option.textContent = value;
            select.appendChild(option);
        });
    });

    // --- Bloco 4: Lógica de Filtro de Dados (Atualizada) ---
    const currentFilters = {};
    filterSelects.forEach(select => {
        const colClass = select.getAttribute('data-col');
        currentFilters[colClass] = ""; 
    });

    function applyFilters() {
        dataRows.forEach(row => {
            let rowIsVisible = true;
            const cells = row.querySelectorAll('td');
            
            cells.forEach(cell => {
                const colClass = cell.classList[0];
                const filterValue = currentFilters[colClass];
                
                // PULA o filtro se o filtro for "Todos" (vazio)
                // OU se a coluna estiver oculta (o filtro não deve se aplicar)
                if (filterValue === "" || cell.classList.contains('col-hidden')) {
                    return;
                }
                
                if (cell.textContent.trim() !== filterValue) {
                    rowIsVisible = false;
                }
            });

            row.style.display = rowIsVisible ? "" : "none";
        });
    }

    filterSelects.forEach(select => {
        select.addEventListener('change', function() {
            const colClass = this.getAttribute('data-col');
            currentFilters[colClass] = this.value;
            applyFilters();
        });
    });

    // --- Bloco 5: Lógica de Visibilidade (Atualizada) ---
    toggleBtn.addEventListener('click', function() {
        const isHidden = toggleMenu.style.display === 'none';
        toggleMenu.style.display = isHidden ? 'grid' : 'none';
    });

    toggleCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const colClass = this.getAttribute('data-col');
            const cells = document.querySelectorAll(`.${colClass}`); // Pega todos os <th> e <td>
            const header = document.querySelector(`th[data-col="${colClass}"]`); // Pega o <select>
            
            if (!cells.length) return;

            const isHiding = !this.checked;
            const currentTableWidth = table.offsetWidth;
            const headerCell = document.querySelector(`th.${colClass}`); // O <th> principal
            
            // Pega a largura salva para REEXIBIR
            const widthToRestore = parseInt(headerCell.getAttribute('data-last-width') || '150');
            // Pega a largura atual para SUBTRAIR
            const widthToSubtract = headerCell.offsetWidth;
            
            let newTableWidth;
            if (isHiding) {
                newTableWidth = currentTableWidth - widthToSubtract;
            } else {
                newTableWidth = currentTableWidth + widthToRestore;
            }
            
            // Aplica a nova largura total da tabela
            table.style.width = newTableWidth + 'px';

            // Aplica/Remove a classe .col-hidden de todas as células
            cells.forEach(cell => {
                cell.classList.toggle('col-hidden', isHiding);
            });
            
            // Reseta o filtro da coluna que foi oculta/reexibida
            if (header) {
                const filterSelect = document.querySelector(`#filter-row select[data-col="${colClass}"]`);
                if (filterSelect) {
                    filterSelect.value = "";
                    currentFilters[colClass] = "";
                    applyFilters(); // Re-aplica filtros
                }
            }
        });
    });

    // Opcional: Fechar o menu se clicar fora dele
    document.addEventListener('click', function(e) {
        if (!toggleBtn.contains(e.target) && !toggleMenu.contains(e.target)) {
            toggleMenu.style.display = 'none';
        }
    });

});