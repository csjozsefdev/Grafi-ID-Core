interface StartupScreenProps {

  loading: boolean;

  errorTitle: string | null;

  errorMessage: string | null;

  onRetry: () => void;

}



export function StartupScreen({

  loading,

  errorTitle,

  errorMessage,

  onRetry,

}: StartupScreenProps) {

  if (loading) {

    return (

      <div className="startup" role="status" aria-busy="true">

        <div className="startup__spinner" aria-hidden="true" />

        <h2>Starting Graf-Id</h2>

        <p>Loading local backend and verifying your database…</p>

        <p className="muted">This usually takes a few seconds on first launch.</p>

      </div>

    );

  }



  if (errorMessage) {

    return (

      <div className="startup startup--error" role="alert">

        <h2>{errorTitle ?? "Startup failed"}</h2>

        <p>{errorMessage}</p>

        <button type="button" className="startup__button" onClick={onRetry}>

          Retry

        </button>

      </div>

    );

  }



  return null;

}

