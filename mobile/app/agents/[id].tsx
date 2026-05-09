import { Redirect } from "expo-router";

/**
 * Legacy agent chat route -- redirects to the main Lucy chat tab.
 * The agents system has been replaced by the Lucy companion.
 */
export default function LegacyAgentRedirect() {
  return <Redirect href="/(tabs)" />;
}
