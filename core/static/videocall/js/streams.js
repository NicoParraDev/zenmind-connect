const APP_ID = '4ac42c9616994b0ebf83a0399dcc56c0'
const TOKEN = sessionStorage.getItem('token')
const CHANNEL = sessionStorage.getItem('room')
let UID = sessionStorage.getItem('UID')
let NAME = sessionStorage.getItem('name')
const client = AgoraRTC.createClient({ mode: 'rtc', codec: 'vp8' })

let localTracks = []
let remoteUsers = {}



var video = document.querySelector('.recording');
var output = document.querySelector('.output');
var start = document.querySelector('.start-btn');
var stop = document.querySelector('.stop-btn');
var anc = document.querySelector(".download-anc")
var data = [];

// In order record the screen with system audio


let toggleShare = async () => {

  alert('💻  Usted va a compartir la pantalla de su dispositivo 💻 ')
  var recording = await navigator.mediaDevices.getDisplayMedia({


    video: {
      mediaSource: 'screen',
    },
    audio: true,
  })

    .then(async (e) => {
      // For recording the mic audio
      let audio = await navigator.mediaDevices.getUserMedia({
        audio: true, video: false
      })
      // Assign the recorded mediastream to the src object 
      video.srcObject = e;

      // Combine both video/audio stream with MediaStream object
      let combine = new MediaStream(
        [...e.getTracks(), ...audio.getTracks()]
      )
      /* Record the captured mediastream
         with MediaRecorder constructor */
      let recorder = new MediaRecorder(combine);
      start.addEventListener('click', (e) => {
        // Starts the recording when clicked
        recorder.start();
        var toastMixin = Swal.mixin({
          toast: true,
          icon: 'info',
          iconColor: 'white',
          title: 'General Title',
          customClass: {
            popup: 'colored-toast'
          },
          animation: false,
          position: 'top-right',
          showConfirmButton: false,
          timer: 3000,
          timerProgressBar: true,
          didOpen: (toast) => {
            toast.addEventListener('mouseenter', Swal.stopTimer)
            toast.addEventListener('mouseleave', Swal.resumeTimer)
          }
        });
        toastMixin.fire({
          animation: true,
          title: 'La grabación ha comenzado 🎥🔴'
        });



     


        var audio = document.getElementById("audio8");
        audio.play();

        // For a fresh start
        data = []
      });

      stop.addEventListener('click', (e) => {

        // Stops the recording  
        recorder.stop();
        var toastMixin = Swal.mixin({
          toast: true,
          icon: 'warning',
          iconColor: 'white',
          title: 'General Title',
          customClass: {
            popup: 'colored-toast'
          },
          animation: false,
          position: 'top-right',
          showConfirmButton: false,
          timer: 3000,
          timerProgressBar: true,
          didOpen: (toast) => {
            toast.addEventListener('mouseenter', Swal.stopTimer)
            toast.addEventListener('mouseleave', Swal.resumeTimer)
          }
        });
        toastMixin.fire({
          animation: true,
          title: 'La grabación se ha detenido 🎥 ⏸️'
        });

        var audio = document.getElementById("audio7");
        audio.play();

      });

      /* Push the recorded data to data array 
        when data available */
      recorder.ondataavailable = (e) => {
        data.push(e.data);
      };

      recorder.onstop = () => {




        /* Convert the recorded audio to 
           blob type mp4 media */
        let blobData = new Blob(data, { type: 'video/mp4' });

        // Convert the blob data to a url
        let url = URL.createObjectURL(blobData)

        // Assign the url to the output video tag and anchor 
        output.src = url
        anc.href = url
      };
    });
}



let joinAndDisplayLocalStream = async () => {
  document.getElementById('room-name').innerText = CHANNEL
  client.on('user-published', handleUserJoined)
  client.on('user-left', handleUserLeft)

  try {
    UID = await client.join(APP_ID, CHANNEL, TOKEN, UID)
  } catch (error) {
    console.error(error)
    window.open('/', '_self')
  }

  localTracks = await AgoraRTC.createMicrophoneAndCameraTracks()

  let member = await createMember()


  let player = `<div  class="video-container" id="user-container-${UID}">
                     <div class="video-player" id="user-${UID}"></div>
                     <div class="username-wrapper"><span class="user-name">${member.name}</span></div>
                     <video class="recording" id="recording" autoplay muted width="300px" height="300px"></video>
                  </div>
                  
                  `

  document.getElementById('video-streams').insertAdjacentHTML('beforeend', player)
  localTracks[1].play(`user-${UID}`)
  await client.publish([localTracks[0], localTracks[1]])
}







let handleUserJoined = async (user, mediaType) => {
  remoteUsers[user.uid] = user
  await client.subscribe(user, mediaType)

  if (mediaType === 'video') {
    let player = document.getElementById(`user-container-${user.uid}`)
    if (player != null) {
      player.remove()
    }

    let member = await getMember(user)

    player = `

       
        <div  class="video-container" id="user-container-${user.uid}">
            <div class="video-player" id="user-${user.uid}"></div>
            <div class="username-wrapper"><span class="user-name">${member.name}</span></div>
        </div> 

        
        `




    document.getElementById('video-streams').insertAdjacentHTML('beforeend', player)
    user.videoTrack.play(`user-${user.uid}`)
  }

  if (mediaType === 'audio') {
    user.audioTrack.play()
  }

}













let handleUserLeft = async (user) => {
  var toastMixin = Swal.mixin({
    toast: true,
    icon: 'error',
    iconColor: 'white',
    title: 'General Title',
    customClass: {
      popup: 'colored-toast'
    },
    animation: false,
    position: 'top-right',
    showConfirmButton: false,
    timer: 3000,
    timerProgressBar: true,
    didOpen: (toast) => {
      toast.addEventListener('mouseenter', Swal.stopTimer)
      toast.addEventListener('mouseleave', Swal.resumeTimer)
    }
  });
  toastMixin.fire({
    animation: true,
    title: 'Un usuario se fué de la sala 🛋️'
  });

  var audio = document.getElementById("audio3");
  audio.play();
  delete remoteUsers[user.uid]
  document.getElementById(`user-container-${user.uid}`).remove()
}





let leaveAndRemoveLocalStream = async () => {
  Swal.fire({
    backdrop: "linear-gradient(white, green)",
    title: 'Esperamos que vuelvas pronto',
    text: 'Gracias por querer ser participe de esta nueva iniciativa!',
    showCancelButton: false,
    showConfirmButton: false,
    footer: '<span class="verde">Tu puedes, no estas solo</span>',
    padding: '1rem',
  })
  for (let i = 0; localTracks.length > i; i++) {
    localTracks[i].stop()
    localTracks[i].close()
  }
  await client.leave()
  //This is somewhat of an issue because if user leaves without actaull pressing leave button, it will not trigger
  deleteMember()
  window.open('/', '_self')
}




let toggleCamera = async (e) => {
  console.log('TOGGLE CAMERA TRIGGERED')
  if (localTracks[1].muted) {
    var toastMixin = Swal.mixin({
      toast: true,
      icon: 'info',
      iconColor: 'white',
      title: 'General Title',
      customClass: {
        popup: 'colored-toast'
      },
      animation: false,
      position: 'top-right',
      showConfirmButton: false,
      timer: 3000,
      timerProgressBar: true,
      didOpen: (toast) => {
        toast.addEventListener('mouseenter', Swal.stopTimer)
        toast.addEventListener('mouseleave', Swal.resumeTimer)
      }
    });
    toastMixin.fire({
      animation: true,
      title: 'Camara encendida 🎥'
    });

    var audio = document.getElementById("audio6");
    audio.play();

    await localTracks[1].setMuted(false)
    e.target.style.backgroundColor = '#fff'
  } else {
    var toastMixin = Swal.mixin({
      toast: true,
      icon: 'warning',
      iconColor: 'white',
      title: 'General Title',
      customClass: {
        popup: 'colored-toast'
      },
      animation: false,
      position: 'top-right',
      showConfirmButton: false,
      timer: 3000,
      timerProgressBar: true,
      didOpen: (toast) => {
        toast.addEventListener('mouseenter', Swal.stopTimer)
        toast.addEventListener('mouseleave', Swal.resumeTimer)
      }
    });
    toastMixin.fire({
      animation: true,
      title: 'Camara apagada 🎥'
    });

    var audio = document.getElementById("audio5");
    audio.play();

    await localTracks[1].setMuted(true)
    e.target.style.backgroundColor = 'rgb(255, 80, 80, 1)'
  }
}









let toggleMic = async (e) => {
  if (localTracks[0].muted) {
    var toastMixin = Swal.mixin({
      toast: true,
      icon: 'info',
      iconColor: 'white',
      title: 'General Title',
      customClass: {
        popup: 'colored-toast'
      },
      animation: false,
      position: 'top-right',
      showConfirmButton: false,
      timer: 3000,
      timerProgressBar: true,
      didOpen: (toast) => {
        toast.addEventListener('mouseenter', Swal.stopTimer)
        toast.addEventListener('mouseleave', Swal.resumeTimer)
      }
    });
    toastMixin.fire({
      animation: true,
      title: 'Microfono encendido 🎙️'
    });

    var audio = document.getElementById("audio6");
    audio.play();

    await localTracks[0].setMuted(false)
    e.target.style.backgroundColor = '#fff'
  }
  else {
    var toastMixin = Swal.mixin({
      toast: true,
      icon: 'warning',
      iconColor: 'white',
      title: 'General Title',
      customClass: {
        popup: 'colored-toast'
      },
      animation: false,
      position: 'top-right',
      showConfirmButton: false,
      timer: 3000,
      timerProgressBar: true,
      didOpen: (toast) => {
        toast.addEventListener('mouseenter', Swal.stopTimer)
        toast.addEventListener('mouseleave', Swal.resumeTimer)
      }
    });
    toastMixin.fire({
      animation: true,
      title: 'Microfono apagado 🎙️'
    });

    var audio = document.getElementById("audio5");
    audio.play();

    await localTracks[0].setMuted(true)
    e.target.style.backgroundColor = 'rgb(255, 80, 80, 1)'
  }
}


let createMember = async () => {
  let response = await fetch('/create_member/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ 'name': NAME, 'room_name': CHANNEL, 'UID': UID })
  })
  let member = await response.json()

  var toastMixin = Swal.mixin({
    toast: true,
    icon: 'success',
    iconColor: 'white',
    title: 'General Title',
    customClass: {
      popup: 'colored-toast'
    },
    animation: false,
    position: 'top-right',
    showConfirmButton: false,
    timer: 3000,
    timerProgressBar: true,
    didOpen: (toast) => {
      toast.addEventListener('mouseenter', Swal.stopTimer)
      toast.addEventListener('mouseleave', Swal.resumeTimer)
    }
  });
  toastMixin.fire({
    animation: true,
    title: JSON.stringify(NAME) + ' Has ingresado a la sala 🛋️',
  });
  var audio = document.getElementById("audio");
  audio.play();
  return member
}

let getMember = async (user) => {
  let response = await fetch(`/get_member/?UID=${user.uid}&room_name=${CHANNEL}`)
  let member = await response.json()



  var toastMixin = Swal.mixin({
    toast: true,
    icon: 'info',
    iconColor: 'white',
    title: 'General Title',
    customClass: {
      popup: 'colored-toast'
    },
    animation: false,
    position: 'top-right',
    showConfirmButton: false,
    timer: 3000,
    timerProgressBar: true,
    didOpen: (toast) => {
      toast.addEventListener('mouseenter', Swal.stopTimer)
      toast.addEventListener('mouseleave', Swal.resumeTimer)
    }
  });
  toastMixin.fire({
    animation: true,
    title: 'Un usuario llegó a la sala 👤➕'
  });

  var audio = document.getElementById("audio2");
  audio.play();
  return member
}



let deleteMember = async () => {
  alert('⬅️ Has salido de la sala ⬅️')
  let response = await fetch('/delete_member/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ 'name': NAME, 'room_name': CHANNEL, 'UID': UID })
  })
  let member = await response.json()
  var audio = document.getElementById("audio4");
  audio.play();
  return member
}

















window.addEventListener("afterunload", deleteMember);

joinAndDisplayLocalStream()


document.getElementById('leave-btn').addEventListener('click', leaveAndRemoveLocalStream)
document.getElementById('camera-btn').addEventListener('click', toggleCamera)
document.getElementById('mic-btn').addEventListener('click', toggleMic)






document.getElementById('share-btn').addEventListener('click', toggleShare)























