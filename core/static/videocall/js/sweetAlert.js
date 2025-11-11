swal.fire({
        title:'Bienvenido/a, Cuenta con nosotros!',
        text:'Gracias por querer ser participe de esta nueva iniciativa!',
        confirmButtonText:'Vamos a calmarnos',
        footer:'<span class="verde">Porfavor procura siempre velar por el respeto y un buen ambiente</span>',
        padding: '1rem',
        backdrop: `
        rgba(0,255,0,0.2)
        url("/images/nyan-cat.gif")
        left top
        no-repeat
      `,
        timer: 10000,
        timerProgressBar: true,
        allowOutsideClick: false,
        allowEscapeKey: false,
        allowEnterKey: false,
        ShowConfirmButton: true,
        confirmButtonColor: '#b8d6c5',
        buttonsStyling: true,
        showClosebutton: true,
        closeButtonAriaLabel: 'cerrar ventana',
        imageUrl: '../static/IMG/logo_final.png',
        imageWidth: '200px',
        //imageHeight: '',
        imageAlt: 'Logo del proyecto'
        
        /*icon:'success',*/
        /*icon:'question',*/
        /*icon:'warning',*/
        /*icon:'error',*/
        /*icon:'info',*/
        
    });


