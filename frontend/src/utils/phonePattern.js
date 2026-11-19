// Mirrors kava_varasto.validators.PHONE_RE (the server-side source of
// truth: ^(\+358\d{6,12}|0\d{6,12})$) plus normalize_phone, which the API
// runs before matching it: whitespace is allowed anywhere and stripped
// server-side, so a digit here may be preceded by \s* to accept it too.
// Used as an HTML <input pattern="..."> value, which is implicitly
// anchored, so no ^/$ here.
const PHONE_PATTERN = "\\s*(\\+\\s*3\\s*5\\s*8|0)(\\s*\\d){6,12}\\s*";

export default PHONE_PATTERN;
