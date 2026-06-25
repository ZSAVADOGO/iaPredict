// =========================================================================
// EXPORTATION DE TABLEAU HTML VERS UN FICHIER EXCEL (.XLSX)
// =========================================================================
window.exportHtmlTableToExcel = function(tableId, filename = "Export_Donnees") {
    const tableElement = document.getElementById(tableId);
    if (!tableElement) {
        if (typeof window.alertError === 'function') {
            window.alertError("Impossible de trouver le tableau à exporter.");
        }
        return;
    }

    try {
        // 1. Convertir le tableau HTML visible en objet de feuille de calcul SheetJS
        const worksheet = XLSX.utils.table_to_sheet(tableElement);

        // 2. Créer un nouveau classeur Excel vierge
        const workbook = XLSX.utils.book_new();

        // 3. Insérer la feuille dans le classeur avec le nom "Résultats"
        XLSX.utils.book_append_sheet(workbook, worksheet, "Résultats");

        // 4. Générer le fichier et déclencher le téléchargement automatique dans le navigateur
        XLSX.writeFile(workbook, `${filename}_${new Date().toISOString().slice(0,10)}.xlsx`);
        
    } catch (error) {
        console.error("Erreur d'export Excel :", error);
        if (typeof window.alertError === 'function') {
            window.alertError("Une erreur est survenue lors de la génération du fichier Excel.");
        }
    }
};


// =========================================================================
// 1. FONCTION GLOBALE POUR LA MODIFICATION (Avec extraction et pré-remplissage)
// =========================================================================
window.openEditAgentModal = function(formHtml, buttonElement) {
    const agentId = buttonElement.getAttribute('data-id');
    const agentName = buttonElement.getAttribute('data-name');
    const agentModel = buttonElement.getAttribute('data-model'); 
    const agentApiKey = buttonElement.getAttribute('data-api-key');
    const agentInstruction = buttonElement.getAttribute('data-instruction');
    const isActive = buttonElement.getAttribute('data-active') === 'true';
    const createdAt = buttonElement.getAttribute('data-created');
    const updatedAt = buttonElement.getAttribute('data-updated');

    Swal.fire({
        title: "Modifier l'Agent",
        html: formHtml, 
        showConfirmButton: false, 
        focusConfirm: false,
        width: '450px',
        background: '#ffffff',
        customClass: {
            popup: 'rounded-2xl shadow-2xl p-6'
        },
        allowOutsideClick: true,
        
        didOpen: () => {
            const popup = Swal.getPopup();
            
            const form = popup.querySelector('form');
            if (form) {
                form.action = `/edit/${agentId}/`;
            }

            const createdSpan = popup.querySelector('#edit_created_at');
            if (createdSpan) createdSpan.textContent = createdAt || '—';

            const updatedSpan = popup.querySelector('#edit_updated_at');
            if (updatedSpan) updatedSpan.textContent = updatedAt || '—';

            const nameInput = popup.querySelector('#edit_name');
            if (nameInput) nameInput.value = agentName || '';

            const modelInput = popup.querySelector('#edit_model_name');
            if (modelInput) modelInput.value = agentModel || '';

            const apiKeyInput = popup.querySelector('#edit_api_key');
            if (apiKeyInput) apiKeyInput.value = agentApiKey || '';

            const instructionInput = popup.querySelector('#edit_system_instruction');
            if (instructionInput) {
                if (agentInstruction === "Aucune instruction configurée." || agentInstruction === '""' || !agentInstruction) {
                    instructionInput.value = '';
                } else {
                    instructionInput.value = agentInstruction;
                }
            }

            const activeCheckbox = popup.querySelector('#edit_is_active');
            if (activeCheckbox) activeCheckbox.checked = isActive;
        }
    });
};

// =========================================================================
// FONCTION GLOBALE POUR LA MODIFICATION D'UNE SOURCE DE DONNÉES (DbSource)
// =========================================================================
window.openEditDbSourceModal = function(formHtml, buttonElement) {
    // 1. Extraction de toutes les propriétés depuis le bouton cliqué
    const dbId = buttonElement.getAttribute('data-id');
    const dbName = buttonElement.getAttribute('data-name');
    const dbType = buttonElement.getAttribute('data-type');
    const dbHost = buttonElement.getAttribute('data-host');
    const dbPort = buttonElement.getAttribute('data-port');
    const dbDatabaseName = buttonElement.getAttribute('data-dbname');
    const dbUser = buttonElement.getAttribute('data-user');
    const createdAt = buttonElement.getAttribute('data-created');
    const updatedAt = buttonElement.getAttribute('data-updated');

    // 2. Déclenchement de la modale SweetAlert2
    Swal.fire({
        title: "Modifier la Source de Données",
        html: formHtml,
        showConfirmButton: false,
        focusConfirm: false,
        width: '500px',
        background: '#ffffff',
        customClass: {
            popup: 'rounded-2xl shadow-2xl p-6'
        },
        allowOutsideClick: true,
        
        // 3. Remplissage des configurations dans le DOM de la modale active
        didOpen: () => {
            const popup = Swal.getPopup();
            
            // Mutation dynamique de l'action du formulaire Django
            const form = popup.querySelector('form');
            if (form) {
                form.action = `/edit_source/${dbId}/`; 
            }

            // Remplissage des dates de métadonnées
            const createdSpan = popup.querySelector('.js-edit-created');
            if (createdSpan) createdSpan.textContent = createdAt || '—';

            const updatedSpan = popup.querySelector('.js-edit-updated');
            if (updatedSpan) updatedSpan.textContent = updatedAt || '—';

            // Remplissage des champs de saisie (Inputs)
            const nameInput = popup.querySelector('.js-edit-name');
            if (nameInput) nameInput.value = dbName || '';

            const typeSelect = popup.querySelector('.js-edit-type');
            if (typeSelect) typeSelect.value = dbType || 'mysql';

            const hostInput = popup.querySelector('.js-edit-host');
            if (hostInput) hostInput.value = dbHost || '';

            const portInput = popup.querySelector('.js-edit-port');
            if (portInput) portInput.value = dbPort || '';

            const dbNameInput = popup.querySelector('.js-edit-dbname');
            if (dbNameInput) dbNameInput.value = dbDatabaseName || '';

            const userInput = popup.querySelector('.js-edit-username');
            if (userInput) userInput.value = dbUser || '';

            // Gestion sécurisée du mot de passe (on le force à vide à l'ouverture)
            const passwordInput = popup.querySelector('.js-edit-password');
            if (passwordInput) passwordInput.value = '';
        }
    });
};

/*window.openEditDbSourceModal = function(formHtml, buttonElement) {
    // 1. Extraction de toutes les propriétés du modèle DbSource
    const dbId = buttonElement.getAttribute('data-id');
    const dbName = buttonElement.getAttribute('data-name');
    const dbType = buttonElement.getAttribute('data-type');
    const dbHost = buttonElement.getAttribute('data-host');
    const dbPort = buttonElement.getAttribute('data-port');
    const dbDatabaseName = buttonElement.getAttribute('data-dbname');
    const dbUser = buttonElement.getAttribute('data-user');
    const createdAt = buttonElement.getAttribute('data-created');
    const updatedAt = buttonElement.getAttribute('data-updated');

    // 2. Déclenchement de la modale SweetAlert2
    Swal.fire({
        title: "Modifier la Source de Données",
        html: formHtml,
        showConfirmButton: false,
        focusConfirm: false,
        width: '500px', // Légèrement plus large pour les structures à 2 colonnes
        background: '#ffffff',
        customClass: {
            popup: 'rounded-2xl shadow-2xl p-6'
        },
        allowOutsideClick: true,
        
        // 3. Remplissage asynchrone des configurations réseau dans le DOM actif
        didOpen: () => {
            const popup = Swal.getPopup();
            
            // Mutation de l'action du formulaire (cible l'ID Django de la BDD, adapter le chemin d'URL selon votre urls.py)
            const form = popup.querySelector('form');
            if (form) {
                form.action = `/source/edit/${dbId}/`; 
            }

            // Remplissage des dates miniatures d'audit
            const createdSpan = popup.querySelector('#edit_db_created_at');
            if (createdSpan) createdSpan.textContent = createdAt || '—';

            const updatedSpan = popup.querySelector('#edit_db_updated_at');
            if (updatedSpan) updatedSpan.textContent = updatedAt || '—';

            // Remplissage de l'ensemble des champs réseaux et authentifications
            const nameInput = popup.querySelector('#edit_db_name');
            if (nameInput) nameInput.value = dbName || '';

            const typeSelect = popup.querySelector('#edit_db_type');
            if (typeSelect) typeSelect.value = dbType || 'mysql';

            const hostInput = popup.querySelector('#edit_db_host');
            if (hostInput) hostInput.value = dbHost || '';

            const portInput = popup.querySelector('#edit_db_port');
            if (portInput) portInput.value = dbPort || '';

            const dbNameInput = popup.querySelector('#edit_db_database_name');
            if (dbNameInput) dbNameInput.value = dbDatabaseName || '';

            const userInput = popup.querySelector('#edit_db_username');
            if (userInput) userInput.value = dbUser || '';

            // Le champ mot de passe reste volontairement vide par sécurité
            const passwordInput = popup.querySelector('#edit_db_password');
            if (passwordInput) passwordInput.value = '';
        }
    });
};*/


// =========================================================================
// 2. FONCTION GLOBALE POUR LA CRÉATION (Simple affichage sans pré-remplissage)
// =========================================================================
window.openAgentModal = function(formHtml) {
    Swal.fire({
        title: formHtml.includes('edit_agent') ? "Modifier l'Agent" : "Ajouter un Agent",
        html: formHtml, 
        showConfirmButton: false, 
        focusConfirm: false,
        width: '450px',
        background: '#ffffff',
        customClass: {
            popup: 'rounded-2xl shadow-2xl p-6'
        },
        allowOutsideClick: true,

        didOpen: () => {
            const btnTest = document.getElementById('btn-test-connection');
            const form = document.getElementById('dbSourceRealForm');
            const statusSpan = document.getElementById('connection-status-span');

            if (btnTest) {
                btnTest.onclick = function() {
                    // 1. Rendre le span visible et afficher un état d'attente
                    statusSpan.style.display = "inline-block";
                    statusSpan.style.color = "#b45309"; // Couleur orange de chargement
                    statusSpan.innerText = "Vérification en cours...";

                    // 2. Récupérer les données saisies par l'utilisateur
                    const formData = new FormData(form);

                    // 3. Appel direct de l'URL de votre vue Django (en dur)
                    fetch('/chat/test_connect_bdd/', {
                        method: "POST",
                        body: formData,
                        headers: {
                            "X-Requested-With": "XMLHttpRequest"
                        }
                    })
                    .then(response => response.json().then(data => ({ status: response.status, body: data })))
                    .then(res => {
                        // 4. Afficher la réponse dans le span selon le succès ou l'échec
                        if (res.status === 200 && res.body.success) {
                            statusSpan.style.color = "#15803d"; // Couleur verte
                            statusSpan.innerText = res.body.message;
                        } else {
                            statusSpan.style.color = "#b91c1c"; // Couleur rouge
                            statusSpan.innerText = res.body.message || "Échec de la connexion.";
                        }
                    })
                    .catch(err => {
                        statusSpan.style.color = "#b91c1c";
                        statusSpan.innerText = "Erreur réseau ou serveur inaccessible.";
                    });
                };
            }
        }

    });
};

// =========================================================================
// TRAITEMENT CENTRALISÉ DES MESSAGES DJANGO
// =========================================================================
window.handleDjangoMessage = function(tag, text) {
    if (!text) return;
    
    const cleanTag = tag.trim().toLowerCase();

    if (cleanTag === 'error' || cleanTag.includes('error')) {
        if (typeof window.alertError === 'function') window.alertError(text);
    } 
    else if (cleanTag === 'success' || cleanTag.includes('success')) {
        if (typeof window.alertSuccess === 'function') window.alertSuccess(text);
    } 
    else if (cleanTag === 'warning' || cleanTag.includes('warning')) {
        if (typeof window.alertWarning === 'function') window.alertWarning(text);
    } 
    else {
        if (typeof window.alertInfo === 'function') window.alertInfo(text);
    }
};


// ALERT SUCCESS (Sera appelée pour messages.success)
window.alertSuccess = function(message = "Opération réussie") {
    Swal.fire({
        icon: 'success',
        title: 'Succès',
        text: message,
        confirmButtonColor: '#3085d6'
    });
};

// ALERT ERROR (Sera appelée pour messages.error)
window.alertError = function(message = "Une erreur est survenue") {
    Swal.fire({
        icon: 'error',
        title: 'Erreur',
        text: message,
        confirmButtonColor: '#d33'
    });
};

// ALERT INFO (Sera appelée par défaut pour les autres messages)
window.alertInfo = function(message = "Information") {
    Swal.fire({
        icon: 'info',
        title: 'Information',
        text: message
    });
};

// ALERT WARNING
window.alertWarning = function(message = "Attention") {
    Swal.fire({
        icon: 'warning',
        title: 'Attention',
        text: message
    });
};

// CONFIRM DELETE
window.confirmDelete = function(callback) {
    Swal.fire({
        title: 'Supprimer ?',
        text: "Cette action est irréversible",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Oui supprimer',
        cancelButtonText: 'Annuler'
    }).then((result) => {
        if (result.isConfirmed) {
            callback();
        }
    });
};


window.deleteSource = function(sourceId, buttonElement) {
    if (typeof window.confirmDelete !== 'function') return;

    window.confirmDelete(function() {
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        const csrfToken = csrfInput ? csrfInput.value : "";

        fetch(`/chat/delete_source/${sourceId}/`, {
            method: "POST",
            headers: {
                "X-Requested-With": "XMLHttpRequest",
                "X-CSRFToken": csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // CORRECTION RADICALE : On cible la div principale de la source
                const row = buttonElement.closest('.source-item-row');
                
                if (row) {
                    // 1. Animation de disparition immédiate à l'écran
                    row.style.transition = "all 0.3s ease";
                    row.style.opacity = "0";
                    row.style.transform = "translateX(30px)"; // Glisse vers la droite
                    row.style.height = "0px";
                    row.style.padding = "0px";
                    row.style.marginBottom = "0px";
                    
                    // 2. Suppression définitive de la page après l'animation (sans recharger)
                    setTimeout(() => {
                        row.remove();
                    }, 300);
                }

                // Uniquement la petite alerte de succès (pas de rechargement)
                Swal.fire({
                    icon: 'success',
                    title: data.message,
                    showConfirmButton: false,
                    timer: 1500
                });
            } else {
                Swal.fire('Erreur', data.message, 'error');
            }
        })
        .catch(err => {
            Swal.fire('Erreur', "Le serveur n'a pas répondu correctement.", 'error');
        });
    });
};

// SUpprimer un AGnet IA
window.deleteAgent = function(agentId, buttonElement) {
    if (typeof window.confirmDelete !== 'function') return;

    window.confirmDelete(function() {
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        const csrfToken = csrfInput ? csrfInput.value : "";

        fetch(`/chat/delete/${agentId}/`, {
            method: "POST",
            headers: {
                "X-Requested-With": "XMLHttpRequest",
                "X-CSRFToken": csrfToken,
                "Accept": "application/json"
            }
        })
        // 1. CORRECTION : On force la lecture de la réponse en texte/json pour libérer le réseau
        .then(response => {
            if (!response.ok) {
                throw new Error("Erreur HTTP: " + response.status);
            }
            return response.json(); // Consomme la réponse Django
        })
        // 2. Traitement une fois la réponse entièrement lue
        .then(data => {
            // L'agent a été supprimé en BDD, on nettoie maintenant l'écran
            const row = buttonElement.closest('.agent-item-row');
            
            if (row) {
                // Animation de disparition fluide
                row.style.transition = "all 0.3s ease";
                row.style.opacity = "0";
                row.style.transform = "translateX(30px)";
                row.style.height = "0px";
                row.style.padding = "0px";
                row.style.marginBottom = "0px";
                row.style.border = "none";
                
                // Retrait définitif du code HTML de la page
                setTimeout(() => {
                    row.remove();
                }, 300);
            }

            // Alerte verte de succès de SweetAlert2
            Swal.fire({
                icon: 'success',
                title: data.message || "Agent supprimé avec succès !",
                showConfirmButton: false,
                timer: 1500
            });
        })
        .catch(err => {
            console.error("Détails du plantage :", err);
            Swal.fire('Erreur', "Le serveur n'a pas répondu correctement.", 'error');
        });
    });
};



// ALERT LOADING (Assurez-vous qu'elle est bien présente pour votre script fetch)
window.alertLoading = function(message = "Chargement...") {
    Swal.fire({
        title: message,
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });
};


// ===============================
// ALERT LOADING
// ===============================

function alertLoading(message = "Chargement...") {

    Swal.fire({
        title: message,
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });

}