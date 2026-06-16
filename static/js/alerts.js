// ===============================
// MODAL FORMULAIRE AGENT (Sécurisée contre l'erreur .style)
// ===============================
/* function openAgentModal(targetUrl = null) {
    // 1. On cherche le conteneur masqué dans la page
    const container = document.getElementById('agentFormContainer');
    if (!container) {
        console.error("Le conteneur #agentFormContainer est introuvable.");
        return;
    }

    // 2. On récupère le vrai formulaire physique
    const form = container.querySelector('#agentRealForm');
    if (!form) {
        console.error("Le formulaire #agentRealForm est introuvable.");
        return;
    }

    // Si une URL spécifique est passée (ex: add_agent), on met à jour l'action
    if (targetUrl) {
        form.setAttribute('action', targetUrl);
    }

    // 3. Affichage de l'élément DOM direct dans SweetAlert2
    Swal.fire({
        title: form.getAttribute('action').includes('edit_agent') ? "Modifier l'Agent" : "Ajouter un Agent",
        html: form, // Utilisation de l'objet DOM direct pour éviter les bugs d'IDs fantômes
        showConfirmButton: false,
        focusConfirm: false,
        width: '450px',
        background: '#ffffff',
        customClass: {
            popup: 'rounded-2xl shadow-2xl p-6 font-sans',
            title: 'text-lg font-semibold text-gray-800 border-b pb-3 mb-4 text-left'
        },
        allowOutsideClick: true,
        willClose: () => {
            // Sécurité : Remettre le formulaire dans son conteneur masqué à la fermeture
            container.appendChild(form);
        }
    });
} */

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





// ALERT SUCCESS
function alertSuccess(message = "Opération réussie") {

    Swal.fire({
        icon: 'success',
        title: 'Succès',
        text: message,
        confirmButtonColor: '#3085d6'
    });

}

// ===============================
// ALERT ERROR
// ===============================

function alertError(message = "Une erreur est survenue") {

    Swal.fire({
        icon: 'error',
        title: 'Erreur',
        text: message,
        confirmButtonColor: '#d33'
    });

}

// ===============================
// ALERT INFO
// ===============================

function alertInfo(message = "Information") {

    Swal.fire({
        icon: 'info',
        title: 'Information',
        text: message
    });

}

// ===============================
// ALERT WARNING
// ===============================

function alertWarning(message = "Attention") {

    Swal.fire({
        icon: 'warning',
        title: 'Attention',
        text: message
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