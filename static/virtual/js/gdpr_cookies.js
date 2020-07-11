const cookie_name = "miniconf-icml2020-allow-cookies";
const allow_cookies = Cookies.get(cookie_name);

if (!allow_cookies) {
  $(".gdpr").show();
}
$(".gdpr-btn").on("click", () => {
  Cookies.set(cookie_name, 1, { expires: 7 });
  $(".gdpr").hide();
});
