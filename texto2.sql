CREATE OR REPLACE FUNCTION monto_to_text() RETURNS TRIGGER AS $monto_to_text$
  BEGIN
  	new.x_letras=fu_numero_letras(new.amount_total);
    RETURN NEW;
  END;
$monto_to_text$
LANGUAGE plpgsql;


CREATE TRIGGER monto_to_letras BEFORE UPDATE
    ON account_invoice FOR EACH ROW
    EXECUTE PROCEDURE monto_to_text ();
