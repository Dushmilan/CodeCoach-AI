import "@testing-library/jest-dom/vitest";
import { server } from "./mocks/server";
import { beforeAll, afterEach, afterAll } from "vitest";

if (!Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = () => {};
}

beforeAll(() => server.listen({ onUnhandledRequest: "bypass" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
