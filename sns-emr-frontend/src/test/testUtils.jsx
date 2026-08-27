import React from "react";
import { render } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { ThemeModeProvider } from "../theme/theme";

export function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

export function renderWithRoute(ui, { route = "/", path = "*", theme = false } = {}) {
  const content = (
    <MemoryRouter initialEntries={[route]}>
      <Routes>
        <Route path={path} element={ui} />
      </Routes>
    </MemoryRouter>
  );

  return render(theme ? <ThemeModeProvider>{content}</ThemeModeProvider> : content);
}
