if [ $# -ne 2 ]; then
    echo "USAGE: bash $0 FORMULA_FILE XML_OUT_FILE"
    exit
fi

FORMULA_FILE=$1
XML_OUT_FILE=$2

(
echo "<document>
<category>lp</category>
<solver>CPLEX</solver>
<inputMethod>LP</inputMethod>
<email> insert valid email address </email>
<client><![CDATA[Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.0.0 Safari/537.36@104.167.146.70]]></client>
<priority><![CDATA[long]]></priority>
<email><![CDATA[dsiWithUnitTests@gmail.com]]></email>
<LP><![CDATA["
cat ${FORMULA_FILE}
echo "]]></LP>
<options><![CDATA[]]></options>
<post><![CDATA[display solution variables -
]]></post>
<BAS><![CDATA[]]></BAS>
<MST><![CDATA[]]></MST>
<SOL><![CDATA[]]></SOL>
<comments><![CDATA[]]></comments>
</document>"
) > ${XML_OUT_FILE}
