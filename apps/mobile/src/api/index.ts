import { fetch } from "expo/fetch";
import { createClient } from "./client";
export const api = createClient(process.env.EXPO_PUBLIC_API_BASE_URL, fetch);
