import "./app.css";

const apiBaseUrl = import.meta.env.VITE_API_URL || "http://localhost:5000";

export function App() {
  return (
    <main className="app-shell">
      <section>
        <h1>ADHD Board</h1>
        <p>
          Frontend placeholder powered by React. Configure the API base URL with the{" "}
          <code>VITE_API_URL</code> environment variable (currently{" "}
          <strong>{apiBaseUrl}</strong>).
        </p>
        <p>
          Replace this placeholder with the actual UI once the design is ready. The Docker
          setup is already prepared for building the React bundle.
        </p>
      </section>
    </main>
  );
}
