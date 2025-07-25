// A simple global event bus for auth-related events
import mitt from "mitt";

type AuthEvents = {
  // Emitted when a logout is triggered globally (e.g. expired session)
  logout: undefined;
};

const authEvents = mitt<AuthEvents>();
export default authEvents;
