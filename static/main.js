var modal_user = document.getElementById("username-modal");

var btn_user = document.getElementById("change-username");

var span_user = document.getElementsByClassName("close")[0];

var modal_pass = document.getElementById("password-modal");

var btn_pass = document.getElementById("change-password");

var span_pass = document.getElementsByClassName("close")[1];

btn_user.onclick = function() {
  modal_user.style.display = "block";
}
span_user.onclick = function() {
  modal_user.style.display = "none";
}
btn_pass.onclick = function() {
  modal_pass.style.display = "block";
}
span_pass.onclick = function() {
  modal_pass.style.display = "none";
}
window.onclick = function(event) {
  if (event.target == modal_user) {
    modal_user.style.display = "none";
  }
  if (event.target == modal_pass) {
    modal_pass.style.display = "none";
  }
}
