from django import template

register = template.Library();

### FILTER: mrange -- used to render the ||| lines in the channel tree

def mrange( value ):
	"If value > 1, returns range( value - 1 ), else returns an empty list."
	val = int( value );
	if( val > 1 ):
		return range( val - 1 );
	return list();

register.filter( 'mrange', mrange );


