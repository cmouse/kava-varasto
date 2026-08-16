import { getCookie } from "../api/cookies";
import scriptName from "../utils/scriptName";

function LanguageSwitcher() {
  return (
    <form
      action={`${scriptName}/i18n/setlang/`}
      method="post"
      className="d-flex align-items-center gap-1"
    >
      <input type="hidden" name="csrfmiddlewaretoken" value={getCookie("csrftoken")} />
      <input type="hidden" name="next" value={window.location.pathname} />
      <button className="btn btn-sm btn-outline-secondary" type="submit" name="language" value="fi">
        FI
      </button>
      <button className="btn btn-sm btn-outline-secondary" type="submit" name="language" value="en">
        EN
      </button>
    </form>
  );
}

export default LanguageSwitcher;
