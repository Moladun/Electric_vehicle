'use strict';
window.addEventListener('load', function () {
  document.getElementById('log-out').onclick = function () {
    firebase.auth().signOut();
  };
  // FirebaseUI config.
  var uiConfig = {
    signInSuccessUrl: '/',
    signInOptions: [
      firebase.auth.EmailAuthProvider.PROVIDER_ID,
    ],
    // Terms of service url.
    tosUrl: '<your-tos-url>'
  };


  firebase.auth().onAuthStateChanged(function (user) {
    if (user) {
      // User is signed in, so display the "sign out" button and login info.
      document.getElementById('login').hidden = true;
      document.getElementById('log-out').classList.remove('hide')
      // document.getElementById('add-ev').hidden = false;
      document.getElementById('add-ev').classList.remove('hide')
      if (document.getElementById('commentForm'))
        document.getElementById('commentForm').classList.remove('hide')
      if (document.getElementById('deletebtn'))
        document.getElementById('deletebtn').classList.remove('hide')
      if (document.getElementById('editbtn'))
        document.getElementById('editbtn').classList.remove('hide')
      document.getElementById('user-info').innerHTML = "Logged in as "+user.email +" |";
   
      console.log(`Signed in as ${user.displayName} (${user.email})`);
      user.getIdToken().then(function (token) {
        // Add the token to the browser's cookies. The server will then be
        // able to verify the token against the API.
        // SECURITY NOTE: As cookies can easily be modified, only put the
        // token (which is verified server-side) in a cookie; do not add other
        // user information.
        document.cookie = "token=" + token;
      });
    } else {
      // User is signed out.
      // Initialize the FirebaseUI Widget using Firebase.
      var ui = new firebaseui.auth.AuthUI(firebase.auth());
      // Show the Firebase login button.
      ui.start('#firebaseui-auth-container', uiConfig);
      // Update the login state indicators.
      // document.getElementById('deletebtn').classList.add('hide')
      // document.getElementById('editbtn').classList.add('hide')
      document.getElementById('log-out').classList.add('hide');
      document.getElementById('add-ev').classList.add('hide');
      document.getElementById('user-info').hidden = true;
      // Clear the token cookie.
      document.cookie = "token=";
    }
  }, function (error) {
    console.log(error);
    alert('Unable to log in: ' + error)


  });

});

const editForm = document.querySelectorAll('.inputEdit');
document.getElementById('updatebtn').hidden = true;
document.getElementById('editbtn').onclick = () =>{
  document.getElementById('updatebtn').hidden = false;
  document.getElementById('editbtn').hidden= true;
  editForm.forEach(item =>{
    item.disabled = false;
  });
};

