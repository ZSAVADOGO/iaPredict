// Variable globale pour modifier facilement la durée par défaut de toutes les alertes (en millisecondes)
const DEFAULT_ALERT_DURATION = 4000; // 4000 ms = 4 secondes

// ===============================
// MODAL FORMULAIRE DATA SOURCE (SweetAlert2)
// ===============================
function openSourceModal(targetUrl, triggerElement = null) {
    const template = document.getElementById('dbSourceFormTemplate');
    if (!template) return;

    // 1. Cloner le formulaire HTML du template sans toucher à l'original
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = template.innerHTML;
    const form = tempDiv.querySelector('#dbSourceRealForm');
    
    // Fixer l'URL d'action de Django (add_source ou edit_source)
    form.setAttribute('action', targetUrl);

    let modalTitle = "Ajouter une Source de Données";

    // 2. Si c'est une modification et qu'on a passé l'élément cliqué
    if (targetUrl.includes('edit') && triggerElement) {
        modalTitle = "Modifier la Source de Données";
        
        // Remplissage immédiat via les attributs data- du bouton
        tempDiv.querySelector('#modal_name').value = triggerElement.dataset.name || '';
        tempDiv.querySelector('#modal_db_type').value = triggerElement.dataset.dbtype || 'mysql';
        tempDiv.querySelector('#modal_host').value = triggerElement.dataset.host || '';
        tempDiv.querySelector('#modal_database_name').value = triggerElement.dataset.dbname || '';
        tempDiv.querySelector('#modal_port').value = triggerElement.dataset.port || '';
        tempDiv.querySelector('#modal_username').value = triggerElement.dataset.username || '';
        
        // Le mot de passe n'est pas obligatoire en modification
        const passwordInput = tempDiv.querySelector('#modal_password');
        if (passwordInput) passwordInput.required = False;
    }

    // 3. Affichage immédiat (0ms d'attente)
    Swal.fire({
        title: modalTitle,
        html: tempDiv.innerHTML,
        showConfirmButton: false,
        focusConfirm: false,
        width: '560px', // Largeur optimisée pour vos col-md-6 horizontaux
        background: '#ffffff',
        padding: '1.5rem',
        customClass: {
            popup: 'rounded-2xl shadow-2xl font-sans',
            title: 'text-lg font-semibold text-gray-800 border-b pb-3 mb-2 text-left'
        },
        allowOutsideClick: true
    });
}




// ===============================
// MODAL FORMULAIRE AGENT (SweetAlert2)
// ===============================
function openAgentModal(formHtml) {
    Swal.fire({
        title: formHtml.includes('edit_agent') ? "Modifier l'Agent" : "Ajouter un Agent",
        html: formHtml, // Injection de votre formulaire Django
        showConfirmButton: false, // On masque le bouton de base de Swal car votre formulaire a son propre bouton
        focusConfirm: false,
        width: '450px',
        background: '#ffffff',
        customClass: {
            popup: 'rounded-2xl shadow-2xl p-6'
        },
        allowOutsideClick: true
    });
}





// ===============================
// ALERT SUCCESS (Fermeture automatique)
// ===============================
function alertSuccess(message = "Opération réussie", duration = DEFAULT_ALERT_DURATION) {
    Swal.fire({
        icon: 'success',
        title: 'Succès',
        text: message,
        confirmButtonColor: '#3085d6',
        timer: duration,                  // Durée avant fermeture
        timerProgressBar: true,          // Barre de progression visuelle
        showConfirmButton: true          // Laisse le bouton au cas où l'utilisateur veut fermer plus vite
    });
}

// ===============================
// ALERT ERROR (Fermeture automatique)
// ===============================
function alertError(message = "Une erreur est survenue", duration = DEFAULT_ALERT_DURATION) {
    Swal.fire({
        icon: 'error',
        title: 'Erreur',
        text: message,
        confirmButtonColor: '#d33',
        timer: duration,
        timerProgressBar: true,
        showConfirmButton: true
    });
}

// ===============================
// ALERT INFO (Fermeture automatique)
// ===============================
function alertInfo(message = "Information", duration = DEFAULT_ALERT_DURATION) {
    Swal.fire({
        icon: 'info',
        title: 'Information',
        text: message,
        timer: duration,
        timerProgressBar: true,
        showConfirmButton: true
    });
}

// ===============================
// ALERT WARNING (Fermeture automatique)
// ===============================
function alertWarning(message = "Attention", duration = DEFAULT_ALERT_DURATION) {
    Swal.fire({
        icon: 'warning',
        title: 'Attention',
        text: message,
        timer: duration,
        timerProgressBar: true,
        showConfirmButton: true
    });
}


// ===============================
// CONFIRM DELETE
// ===============================

function confirmDelete(callback) {

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

}

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