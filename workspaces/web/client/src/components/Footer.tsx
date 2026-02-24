import { AppFooter, Container } from "@mrquentinha/ui";

export function Footer() {
  return (
    <AppFooter className="bg-bg/80">
      <Container className="flex items-center justify-between py-4 text-xs text-muted">
        <p>Mr Quentinha Web Cliente MVP</p>
        <p>Sem autenticacao real no MVP</p>
      </Container>
    </AppFooter>
  );
}
